# GitHub Method Name Analyzer

Esta es una herramienta para extraer y analizar las palabras mas usadas en los metodos de repositorios populares de Python y Java publicados en GitHub. 

La arquitectura tiene 3 partes principales organizadas con Docker Compose.

1. Miner
Es un script en Python que funciona como productor. Lo que hace es consultar a GitHub los repositorios ordenados por cantidad de estrellas y descarga el codigo en formato zip en memoria (sin tocar el disco). Luego entra a los archivos y saca los nombres de los metodos y funciones usando ast para Python y expresiones regulares para Java. Finalmente, separa las palabras considerando notaciones estilo camelCase o snake_case y las publica en Redis.

2. Redis
Actua como el message broker o bus de mensajes temporal entre los contenedores. Ahi se empareja la logica asincronamente.

3. Visualizer
Es una app en Flask que hace de consumidor ininterrumpido. Tiene un hilo en background que siempre lee la data procesada de la lista de Redis a medida que va llegando. Esa data se consolida y se envia a una vista frontend hecha con Chart.js para que todo el ranking se actualice en vivo mediante requests JS por polling. 

Como ejecutarlo

Tienes que tener Docker instalado. Ubicate en la raiz del proyecto y corre:

docker-compose up --build

Cuando el contenedor termine de levantar los contenedores, abri en el navegador:
http://localhost:5000

Ahi ves el grafico recolectando la data en vivo. Arriba en la pantalla hay un campo donde podes cambiar cuantas topN palabras queres que formen el ranking al vuelo.

Decisiones y supuestos

Opte por usar Redis en vez de RabbitMQ porque es mas simple y suficientemente performante para colas en vivo.
Use la libreria ast de parsing directo de python porque es limpia y a prueba de errores. Para Java lo resolvi con regex para evitar arrastrar librerias secundarias y facilitar el armado del contenedor.
Decidi eludir el principal Rate Limit de GitHub bajando los archivos por paquete ZIP y no analizando las ramas o los rest trees, descubri que eso permite arrancar el proceso de forma mucho mas limpia y levanta muchisima cantidad de material para analizar sin cortar la ejecucion.