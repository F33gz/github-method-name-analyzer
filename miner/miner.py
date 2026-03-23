import os
import requests
import redis
import time
import ast
import re
import zipfile
import tempfile

redis_client = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, decode_responses=True)

HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}
if "GITHUB_TOKEN" in os.environ and os.environ["GITHUB_TOKEN"]:
    HEADERS["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"

def split_name(name):
    name = name.replace('_', ' ')
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    name = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', name)
    words = name.lower().split()
    return [w for w in words if w.isalpha() and len(w) > 1]

def get_python_methods(code):
    methods = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('__'):
                    methods.append(node.name)
    except Exception:
        pass
    return methods

def get_java_methods(code):
    methods = []
    pattern = r'(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?[\w\<\>\[\]\?]+\s+(\w+)\s*\('
    for match in re.finditer(pattern, code):
        name = match.group(1)
        if name not in ('if', 'for', 'while', 'switch', 'catch', 'return', 'new', 'assert', 'synchronized'):
            methods.append(name)
    return methods

def get_repos(language, page):
    url = f"https://api.github.com/search/repositories?q=language:{language}&sort=stars&order=desc&page={page}&per_page=10"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get("items", [])
        elif response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            sleep_time = max(reset_time - int(time.time()), 60)
            time.sleep(sleep_time + 5)
        else:
            time.sleep(10)
    except Exception:
        time.sleep(5)
    return []

def process_repository(repo, language):
    owner = repo["owner"]["login"]
    name = repo["name"]
    branch = repo.get("default_branch", "master")
    
    zip_url = f"https://github.com/{owner}/{name}/archive/refs/heads/{branch}.zip"
    try:
        resp = requests.get(zip_url, timeout=15, stream=True)
        if resp.status_code == 200:
            word_count = 0
            with tempfile.NamedTemporaryFile("w+b") as tmp_file:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                tmp_file.seek(0)
                
                with zipfile.ZipFile(tmp_file) as z:
                    ext = ".py" if language == "python" else ".java"
                    valid_files = [info.filename for info in z.infolist() if not info.is_dir() and info.filename.endswith(ext)]
                    valid_files = valid_files[:40]
                    
                    for f in valid_files:
                        code_bytes = z.read(f)
                        try:
                            code = code_bytes.decode('utf-8', errors='ignore')
                            methods = get_python_methods(code) if language == "python" else get_java_methods(code)
                            
                            words_to_push = []
                            for m in methods:
                                words_to_push.extend(split_name(m))
                                
                            if words_to_push:
                                redis_client.lpush("method_words", *words_to_push)
                                time.sleep(0.01)
                        except Exception:
                            pass
                        time.sleep(0.1)
    except Exception:
        pass

def run():
    page = 1
    while True:
        for lang in ["python", "java"]:
            repos = get_repos(lang, page)
            for repo in repos:
                process_repository(repo, lang)
                time.sleep(1)
        page += 1

if __name__ == "__main__":
    time.sleep(5)
    
    MAX_RETRIES = 5
    for i in range(MAX_RETRIES):
        try:
            redis_client.ping()
            break
        except redis.ConnectionError:
            time.sleep(2)
            
    run()
