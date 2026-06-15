import logging
from pymysql import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base

# ==============================================================================
# 🔥 MODO DETECTIVE ACTIVADO (Rayos X para SQLAlchemy)
# Esto imprimirá en consola absolutamente todo lo que Python le envíe a Clever Cloud
# ==============================================================================
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Importar modelos
from app.models.categorias_model import Categoria
from app.models.clientes_model import Cliente
from app.models.producto_model import Producto
from app.models.marcas_model import Marca
from app.models.variantes_model import Variante
from app.models.variante_imagen_model import Imagen
from app.models.ventas_model import Venta
from app.models.atributo_model import Atributo, ValorAtributo
from app.models.lotes_model import Stock
from app.models.proveedores_model import Proveedor
from app.models.pagos_consignacion_model import PagoConsignacion
from app.models.gastos_model import Gasto
from app.models.atributo_categoria_model import AtributoCategoria  # Tabla intermedia

# ==============================================================================
# 1. DATOS MAESTROS (Estructura: Categoría -> Género -> Tipo de Prenda)
# ==============================================================================
categorias_master = [
    {
        "nombre": "Ropa",
        "descripcion": "Ropa en general",
        "genero": "", 
        "hijos": [
            {
                "nombre": "Mujer",
                "descripcion": "Ropa para mujer",
                "genero": "mujer",
                "hijos": [
                    {
                        "nombre": "Faldas", 
                        "descripcion": "Minifaldas, midi, largas",
                        "genero": "mujer",
                        "hijos": [
                            {"nombre": "Minifaldas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Faldas por la rodilla", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Faldas midi", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Faldas largas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Faldas asimétricas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Falda-pantalón", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Vestidos",
                        "genero": "mujer",
                        "hijos": [
                            {"nombre": "Vestidos cortos / Mini", "genero": "mujer"},
                            {"nombre": "Vestidos midi", "genero": "mujer"},
                            {"nombre": "Vestidos largos / Maxi", "genero": "mujer"},
                            {"nombre": "Vestidos vaqueros", "genero": "mujer"},
                            {"nombre": "Vestidos de punto", "genero": "mujer"},
                            {"nombre": "Vestidos camiseros", "genero": "mujer"},
                            {"nombre": "Vestidos formales", "genero": "mujer"},
                            {"nombre": "Vestidos informales", "genero": "mujer"},
                            {"nombre": "Vestidos sin tirantes", "genero": "mujer"},
                            {"nombre": "Vestidos negros", "genero": "mujer"},
                            {"nombre": "Vestidos de verano / Playeros", "genero": "mujer"},
                            {"nombre": "Vestidos de invierno", "genero": "mujer"},
                            {
                                "nombre": "Ocasiones especiales",
                                "genero": "mujer",
                                "hijos": [
                                    {"nombre": "Vestidos de fiesta y cóctel", "genero": "mujer"},
                                    {"nombre": "Vestidos de novia", "genero": "mujer"},
                                    {"nombre": "Vestidos de graduación", "genero": "mujer"},
                                    {"nombre": "Vestidos de noche", "genero": "mujer"},
                                    {"nombre": "Espalda descubierta", "genero": "mujer"},
                                ]
                            },
                            {"nombre": "Otros vestidos", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Camisetas y tops",
                        "descripcion": "Camisas, blusas, tops",
                        "genero": "mujer",
                        "hijos": [
                            {"nombre": "Camisas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "blusas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "chalecos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Camisetas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Sin mangas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Túnicas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Crop tops", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Manga corta", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Manga 3/4", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Manga Larga", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Bodies", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Hombros descubiertos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Cuello alto", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Peplum", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Halter", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Otros tops", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Vaqueros",
                        "descripcion": "Partes de abajo",
                        "genero": "mujer", 
                        "hijos": [
                            {"nombre": "Vaqueros boyfriend", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Vaqueros tobilleros", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Vaqueros de campana", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Vaqueros de cintura alta", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Vaqueros rotos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Vaqueros pitillo", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Vaqueros rectos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Otros Vaqueros", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Pantalones y leggins",
                        "descripcion": "",
                        "genero": "mujer", 
                        "hijos": [
                            {"nombre": "Pantalones tobilleros y chinos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pantalones anchos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pantalones ptitillo", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pantalones de pinzas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pantalones rectos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pantalones de cuero", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Leggins", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pantalones harén", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Otros Pantalones", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Shorts",
                        "descripcion": "",
                        "genero": "mujer", 
                        "hijos": [
                            {"nombre": "De cintura baja", "descripcion": "", "genero": "mujer"},
                            {"nombre": "De cintura alta", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Hasta la rodilla", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Vaqueros cortos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "De encaje", "descripcion": "", "genero": "mujer"},
                            {"nombre": "De cuero cortos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Estilo cargo mujer", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Capri", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Otros shorts", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Monos",
                        "descripcion": "",
                        "genero": "mujer", 
                        "hijos": [
                            {"nombre": "Monos largos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Monos cortos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Otros monos", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Abrigos y Chaquetas",
                        "descripcion": "Prendas de exterior",
                        "genero": "mujer", 
                        "hijos": [
                            {
                                "nombre": "Abrigos",
                                "genero": "mujer",
                                "hijos": [
                                    {"nombre": "Trencas", "genero": "mujer"},
                                    {"nombre": "Sobretodos y abrigos largos", "genero": "mujer"},
                                    {"nombre": "Parkas", "genero": "mujer"},
                                    {"nombre": "Chaquetones marineros", "genero": "mujer"},
                                    {"nombre": "Impermeables", "genero": "mujer"},
                                    {"nombre": "Gabardinas", "genero": "mujer"},
                                ]
                            },
                            {"nombre": "Chalecos", "genero": "mujer"},
                            {
                                "nombre": "Chaquetas",
                                "genero": "mujer",
                                "hijos": [
                                    {"nombre": "Cazadoras bikers", "genero": "mujer"},
                                    {"nombre": "Chaquetas bombers", "genero": "mujer"},
                                    {"nombre": "Cazadoras vaqueras", "genero": "mujer"},
                                    {"nombre": "Chaquetas militares y utilitarias", "genero": "mujer"},
                                    {"nombre": "Forros polares", "genero": "mujer"},
                                    {"nombre": "Chaquetas harrington", "genero": "mujer"},
                                    {"nombre": "Chaquetas de plumas", "genero": "mujer"},
                                    {"nombre": "Chaquetas acolchadas", "genero": "mujer"},
                                    {"nombre": "Sobrecamisas", "genero": "mujer"},
                                    {"nombre": "Chaquetas de esquí y snow", "genero": "mujer"},
                                    {"nombre": "Chaquetas universitarias", "genero": "mujer"},
                                    {"nombre": "Cortavientos", "genero": "mujer"},
                                ]
                            },
                            {"nombre": "Ponchos", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Jerséis y sudaderas",
                        "descripcion": "",
                        "genero": "mujer",
                        "hijos": [
                            {"nombre": "Sudaderas con capucha", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Sudaderas sin capucha", "descripcion": "", "genero": "mujer"},
                            {
                                "nombre": "Jerséis", 
                                "descripcion": "Jerséis de punto", 
                                "genero": "mujer",
                                "hijos": [
                                    {"nombre": "Cuello alto", "descripcion": "Turtleneck", "genero": "mujer"},
                                    {"nombre": "Cuello de pico", "descripcion": "Escote en V", "genero": "mujer"},
                                    {"nombre": "Cuello redondo", "descripcion": "Crew neck", "genero": "mujer"},
                                    {"nombre": "Jerséis largos", "descripcion": "Tipo túnica o oversize", "genero": "mujer"},
                                    {"nombre": "Jerséis de punto fino", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Jerséis de punto grueso", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Manga 3/4", "descripcion": "", "genero": "mujer"},
                                ]
                            },
                            {"nombre": "Kimonos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Cárdigan", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Boleros", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Chalecos de punto", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Trajes y blazers",
                        "descripcion": "",
                        "genero": "mujer",
                        "hijos": [
                            {"nombre": "Blazers", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Trajes de pantalón", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Trajes de falda", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Ropa de baño",
                        "descripcion": "Playa y piscina",
                        "genero": "mujer",
                        "hijos": [
                            {"nombre": "Bikinis", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Bañadores", "descripcion": "Una pieza o short", "genero": "mujer"},
                            {"nombre": "Trikinis", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pareos y caftanes", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Lencería y pijamas",
                        "descripcion": "",
                        "genero": "mujer", 
                        "hijos": [
                            {"nombre": "Sujetadores", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Braguitas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Conjuntos de lencería", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Lencería moldeadora", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pijamas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Batas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Medias", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Calcetines", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Accesorios de lencería", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Premamá",
                        "descripcion": "",
                        "genero": "mujer", 
                        "hijos": [
                            {"nombre": "Camisetas y blusas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Vestidos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Faldas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pantalones", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Shorts", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Monos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Sudaderas y jerseís", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Abrigos y cazadoras", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Bañadores y pareos", "descripcion": "", "genero": "mujer"},
                            {
                                "nombre": "Ropa interior", 
                                "descripcion": "", 
                                "genero": "mujer",
                                "hijos":[
                                    {"nombre": "Braguitas", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Pijamas", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Sujetadores y posparto", "descripcion": "", "genero": "mujer"},
                                ]
                            },
                            {"nombre": "Ropa de deporte", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Ropa deportiva",
                        "descripcion": "",
                        "genero": "mujer", 
                        "hijos": [
                            {"nombre": "Tops y camisetas deportivas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Sujetadores deportivos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Leggins y pantalones deportivos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Chándales", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Shorts deportivos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Faldas deportivas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Sudaderas deportivas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Chaquetas deportivas", "descripcion": "", "genero": "mujer"},
                        ]
                    }
                ]
            },
            {
                "nombre": "Hombre",
                "descripcion": "Ropa para hombre",
                "genero": "hombre",
                "hijos": [
                    {
                        "nombre": "Camisetas y camisas",
                        "descripcion": "",
                        "genero": "hombre", 
                        "hijos": [
                            {
                                "nombre": "Camisas", 
                                "descripcion": "", 
                                "genero": "hombre",
                                "hijos":[
                                    {"nombre": "Camisas de cuadros", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Camisas vaqueras", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Camisas lisas", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Camisas estampadas", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Camisas de rayas", "descripcion": "", "genero": "hombre"},
                                ]
                            },
                            {
                                "nombre": "Camisetas", 
                                "descripcion": "", 
                                "genero": "hombre",
                                "hijos":[
                                    {"nombre": "Camisetas lisas", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Camisetas estampadas", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Camisetas de rayas", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Camisetas de manga larga", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Camisetas cuello redondo", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Camisetas cuello v", "descripcion": "", "genero": "hombre"},
                                ]
                            },
                            {"nombre": "Polos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Henley", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Camisetas sin mangas", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Vaqueros",
                        "descripcion": "Partes de abajo",
                        "genero": "hombre", 
                        "hijos": [
                            {"nombre": "Vaqueros ajustados / Skinny", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Vaqueros rectos / Straight", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Vaqueros sueltos / Relaxed", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Vaqueros rotos", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Pantalones",
                        "descripcion": "",
                        "genero": "hombre", 
                        "hijos": [
                            {"nombre": "Chinos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Joggers", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pantalones pitillos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pantalones de pinzas / Vestir", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pantalones cargo", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Shorts",
                        "descripcion": "",
                        "genero": "hombre", 
                        "hijos": [
                            {"nombre": "Bermudas vaqueras", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Bermudas chinas", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Shorts de chándal", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Estilo cargo hombre", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Abrigos y Chaquetas",
                        "descripcion": "Prendas de exterior",
                        "genero": "hombre", 
                        "hijos": [
                            {
                                "nombre": "Abrigos",
                                "genero": "hombre",
                                "hijos": [
                                    {"nombre": "Trencas", "genero": "hombre"},
                                    {"nombre": "Sobretodos", "genero": "hombre"},
                                    {"nombre": "Parkas", "genero": "hombre"},
                                    {"nombre": "Chaquetones marineros", "genero": "hombre"},
                                    {"nombre": "Impermeables y Gabardinas", "genero": "hombre"},
                                ]
                            },
                            {"nombre": "Chalecos acolchados", "genero": "hombre"},
                            {
                                "nombre": "Chaquetas",
                                "genero": "hombre",
                                "hijos": [
                                    {"nombre": "Cazadoras bikers de cuero", "genero": "hombre"},
                                    {"nombre": "Chaquetas bombers", "genero": "hombre"},
                                    {"nombre": "Cazadoras vaqueras", "genero": "hombre"},
                                    {"nombre": "Chaquetas militares", "genero": "hombre"},
                                    {"nombre": "Forros polares", "genero": "hombre"},
                                    {"nombre": "Chaquetas harrington", "genero": "hombre"},
                                    {"nombre": "Plumíferos", "genero": "hombre"},
                                    {"nombre": "Sobrecamisas", "genero": "hombre"},
                                    {"nombre": "Cortavientos", "genero": "hombre"},
                                ]
                            },
                        ]
                    },
                    {
                        "nombre": "Jerséis y sudaderas",
                        "descripcion": "",
                        "genero": "hombre",
                        "hijos": [
                            {"nombre": "Sudaderas con capucha", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Sudaderas sin capucha", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Cárdigans", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Jerséis", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Sudaderas con cremallera", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Cuello redondo", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Cuello pico", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Cuello alto", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Largos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "De punto", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Otros", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Trajes y blazers",
                        "descripcion": "",
                        "genero": "hombre",
                        "hijos": [
                            {"nombre": "Blazers y Americanas", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pantalones de traje", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Chalecos de traje", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Trajes completos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Trajes de boda / Esmoquin", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Ropa Interior",
                        "descripcion": "",
                        "genero": "hombre", 
                        "hijos": [
                            {"nombre": "Calzoncillos Slip", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Calzoncillos Boxer", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Camisetas interiores", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Calcetines", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Pijamas",
                        "descripcion": "",
                        "genero": "hombre", 
                        "hijos": [
                            {"nombre": "Pantalones de pijama", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pijamas completos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Albornoces y batas", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Ropa de baño",
                        "descripcion": "Playa y piscina",
                        "genero": "hombre",
                        "hijos": [
                            {"nombre": "Bañadores tipo short", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Bañadores slip", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Ropa deportiva",
                        "descripcion": "",
                        "genero": "hombre", 
                        "hijos": [
                            {"nombre": "Camisetas de entrenamiento", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Camisetas de equipos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Chándales completos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pantalones deportivos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Shorts deportivos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Sudaderas deportivas", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Chaquetas deportivas", "descripcion": "", "genero": "hombre"},
                        ]
                    }
                ]
            },
            {
                "nombre": "Niñas",
                "descripcion": "Ropa para niñas",
                "genero": "niña",
                "hijos": [
                    {
                        "nombre": "Camisetas y tops", 
                        "descripcion": "", 
                        "genero": "niña",
                        "hijos": [
                            {"nombre": "Camisetas de manga corta", "descripcion": "", "genero": "niña"},
                            {"nombre": "Camisetas de manga larga", "descripcion": "", "genero": "niña"},
                            {"nombre": "Blusas y camisas", "descripcion": "", "genero": "niña"},
                            {"nombre": "Tops de tirantes", "descripcion": "", "genero": "niña"},
                            {"nombre": "Tops deportivos", "descripcion": "", "genero": "niña"}
                        ]
                    },
                    {
                        "nombre": "Vestidos y faldas", 
                        "descripcion": "", 
                        "genero": "niña",
                        "hijos": [
                            {"nombre": "Vestidos de verano / casual", "descripcion": "", "genero": "niña"},
                            {"nombre": "Vestidos de fiesta / ceremonia", "descripcion": "", "genero": "niña"},
                            {"nombre": "Faldas vaqueras", "descripcion": "", "genero": "niña"},
                            {"nombre": "Faldas de tul", "descripcion": "", "genero": "niña"},
                            {"nombre": "Faldas pantalón", "descripcion": "", "genero": "niña"}
                        ]
                    },
                    {
                        "nombre": "Pantalones y vaqueros", 
                        "descripcion": "", 
                        "genero": "niña",
                        "hijos": [
                            {"nombre": "Vaqueros / Jeans", "descripcion": "", "genero": "niña"},
                            {"nombre": "Leggings", "descripcion": "", "genero": "niña"},
                            {"nombre": "Pantalones de chándal / Joggers", "descripcion": "", "genero": "niña"},
                            {"nombre": "Pantalones cortos / Shorts", "descripcion": "", "genero": "niña"},
                            {"nombre": "Monos y petos", "descripcion": "", "genero": "niña"}
                        ]
                    },
                    {
                        "nombre": "Jerséis y sudaderas", 
                        "descripcion": "", 
                        "genero": "niña",
                        "hijos": [
                            {"nombre": "Sudaderas con capucha", "descripcion": "", "genero": "niña"},
                            {"nombre": "Sudaderas sin capucha", "descripcion": "", "genero": "niña"},
                            {"nombre": "Jerséis de punto", "descripcion": "", "genero": "niña"},
                            {"nombre": "Cárdigans y chaquetas de punto", "descripcion": "", "genero": "niña"}
                        ]
                    },
                    {
                        "nombre": "Abrigos y chaquetas", 
                        "descripcion": "", 
                        "genero": "niña",
                        "hijos": [
                            {"nombre": "Abrigos y trencas", "descripcion": "", "genero": "niña"},
                            {"nombre": "Cazadoras de entretiempo", "descripcion": "", "genero": "niña"},
                            {"nombre": "Cazadoras vaqueras", "descripcion": "", "genero": "niña"},
                            {"nombre": "Plumíferos y acolchados", "descripcion": "", "genero": "niña"},
                            {"nombre": "Chalecos", "descripcion": "", "genero": "niña"},
                            {"nombre": "Chubasqueros / Impermeables", "descripcion": "", "genero": "niña"}
                        ]
                    },
                    {
                        "nombre": "Ropa de baño", 
                        "descripcion": "", 
                        "genero": "niña",
                        "hijos": [
                            {"nombre": "Bañadores", "descripcion": "", "genero": "niña"},
                            {"nombre": "Bikinis", "descripcion": "", "genero": "niña"},
                            {"nombre": "Culetines", "descripcion": "", "genero": "niña"}
                        ]
                    },
                    {
                        "nombre": "Ropa interior y pijamas", 
                        "descripcion": "", 
                        "genero": "niña",
                        "hijos": [
                            {"nombre": "Braguitas", "descripcion": "", "genero": "niña"},
                            {"nombre": "Camisetas interiores", "descripcion": "", "genero": "niña"},
                            {"nombre": "Calcetines y leotardos", "descripcion": "", "genero": "niña"},
                            {"nombre": "Pijamas de verano", "descripcion": "", "genero": "niña"},
                            {"nombre": "Pijamas de invierno", "descripcion": "", "genero": "niña"},
                            {"nombre": "Batas", "descripcion": "", "genero": "niña"}
                        ]
                    }
                ]
            },
            {
                "nombre": "Niños",
                "descripcion": "Ropa para niños",
                "genero": "niño",
                "hijos": [
                    {
                        "nombre": "Camisetas y camisas", 
                        "descripcion": "", 
                        "genero": "niño",
                        "hijos": [
                            {"nombre": "Camisetas de manga corta", "descripcion": "", "genero": "niño"},
                            {"nombre": "Camisetas de manga larga", "descripcion": "", "genero": "niño"},
                            {"nombre": "Polos", "descripcion": "", "genero": "niño"},
                            {"nombre": "Camisas casuales", "descripcion": "", "genero": "niño"},
                            {"nombre": "Camisas de vestir / ceremonia", "descripcion": "", "genero": "niño"}
                        ]
                    },
                    {
                        "nombre": "Pantalones y vaqueros", 
                        "descripcion": "", 
                        "genero": "niño",
                        "hijos": [
                            {"nombre": "Vaqueros / Jeans", "descripcion": "", "genero": "niño"},
                            {"nombre": "Pantalones chinos", "descripcion": "", "genero": "niño"},
                            {"nombre": "Pantalones de chándal / Joggers", "descripcion": "", "genero": "niño"},
                            {"nombre": "Bermudas y pantalones cortos", "descripcion": "", "genero": "niño"},
                            {"nombre": "Petos", "descripcion": "", "genero": "niño"}
                        ]
                    },
                    {
                        "nombre": "Jerséis y sudaderas", 
                        "descripcion": "", 
                        "genero": "niño",
                        "hijos": [
                            {"nombre": "Sudaderas con capucha", "descripcion": "", "genero": "niño"},
                            {"nombre": "Sudaderas sin capucha", "descripcion": "", "genero": "niño"},
                            {"nombre": "Jerséis de punto", "descripcion": "", "genero": "niño"},
                            {"nombre": "Cárdigans", "descripcion": "", "genero": "niño"}
                        ]
                    },
                    {
                        "nombre": "Abrigos y chaquetas", 
                        "descripcion": "", 
                        "genero": "niño",
                        "hijos": [
                            {"nombre": "Abrigos y trencas", "descripcion": "", "genero": "niño"},
                            {"nombre": "Cazadoras y chaquetas", "descripcion": "", "genero": "niño"},
                            {"nombre": "Cazadoras vaqueras", "descripcion": "", "genero": "niño"},
                            {"nombre": "Plumíferos y parkas", "descripcion": "", "genero": "niño"},
                            {"nombre": "Chalecos", "descripcion": "", "genero": "niño"},
                            {"nombre": "Cortavientos e impermeables", "descripcion": "", "genero": "niño"}
                        ]
                    },
                    {
                        "nombre": "Ropa de baño", 
                        "descripcion": "", 
                        "genero": "niño",
                        "hijos": [
                            {"nombre": "Bañadores tipo short", "descripcion": "", "genero": "niño"},
                            {"nombre": "Bañadores tipo slip", "descripcion": "", "genero": "niño"}
                        ]
                    },
                    {
                        "nombre": "Ropa interior y pijamas", 
                        "descripcion": "", 
                        "genero": "niño",
                        "hijos": [
                            {"nombre": "Calzoncillos (Slips y Boxers)", "descripcion": "", "genero": "niño"},
                            {"nombre": "Camisetas interiores", "descripcion": "", "genero": "niño"},
                            {"nombre": "Calcetines", "descripcion": "", "genero": "niño"},
                            {"nombre": "Pijamas de verano", "descripcion": "", "genero": "niño"},
                            {"nombre": "Pijamas de invierno", "descripcion": "", "genero": "niño"},
                            {"nombre": "Batas", "descripcion": "", "genero": "niño"}
                        ]
                    }
                ]
            },
            {
                "nombre": "Bebés",
                "descripcion": "Ropa para bebés (0-36 meses)",
                "genero": "bebé",
                "hijos": [
                    {
                        "nombre": "Bodys y ropa interior", 
                        "descripcion": "", 
                        "genero": "bebé",
                        "hijos": [
                            {"nombre": "Bodys manga corta", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Bodys manga larga", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Bodys de tirantes", "descripcion": "", "genero": "bebé"}
                        ]
                    },
                    {
                        "nombre": "Peleles y ranitas", 
                        "descripcion": "Prendas de una sola pieza", 
                        "genero": "bebé",
                        "hijos": [
                            {"nombre": "Peleles cortos / de verano", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Peleles largos / de invierno", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Ranitas y petos", "descripcion": "", "genero": "bebé"}
                        ]
                    },
                    {
                        "nombre": "Conjuntos", 
                        "descripcion": "", 
                        "genero": "bebé",
                        "hijos": [
                            {"nombre": "Conjuntos de algodón", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Conjuntos de punto", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Conjuntos de vestir / ceremonia", "descripcion": "", "genero": "bebé"}
                        ]
                    },
                    {
                        "nombre": "Tops y jerséis", 
                        "descripcion": "", 
                        "genero": "bebé",
                        "hijos": [
                            {"nombre": "Camisetas cruzadas", "descripcion": "Fáciles de poner", "genero": "bebé"},
                            {"nombre": "Camisetas normales", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Blusas y camisas", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Jerséis y chaquetas de punto", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Sudaderas", "descripcion": "", "genero": "bebé"}
                        ]
                    },
                    {
                        "nombre": "Pantalones y braguitas", 
                        "descripcion": "", 
                        "genero": "bebé",
                        "hijos": [
                            {"nombre": "Polainas", "descripcion": "Pantalones con pie incluido", "genero": "bebé"},
                            {"nombre": "Leggings infantiles", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Pantalones suaves", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Vaqueros de bebé", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Cubrepañales y braguitas", "descripcion": "", "genero": "bebé"}
                        ]
                    },
                    {
                        "nombre": "Vestidos y faldas", 
                        "descripcion": "", 
                        "genero": "bebé",
                        "hijos": [
                            {"nombre": "Vestidos casuales", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Vestidos de ceremonia", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Faldas", "descripcion": "", "genero": "bebé"}
                        ]
                    },
                    {
                        "nombre": "Ropa de abrigo", 
                        "descripcion": "", 
                        "genero": "bebé",
                        "hijos": [
                            {"nombre": "Buzos para nieve", "descripcion": "Cuerpo entero", "genero": "bebé"},
                            {"nombre": "Abrigos y chaquetones", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Cazadoras", "descripcion": "", "genero": "bebé"}
                        ]
                    },
                    {
                        "nombre": "Pijamas y sacos de dormir", 
                        "descripcion": "", 
                        "genero": "bebé",
                        "hijos": [
                            {"nombre": "Pijamas de cuerpo entero (enterizos)", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Pijamas de dos piezas", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Sacos de dormir", "descripcion": "Para la cuna", "genero": "bebé"}
                        ]
                    },
                    {
                        "nombre": "Ropa de baño", 
                        "descripcion": "", 
                        "genero": "bebé",
                        "hijos": [
                            {"nombre": "Bañadores pañal", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Bañadores y bikinis", "descripcion": "", "genero": "bebé"},
                            {"nombre": "Camisetas de protección solar UV", "descripcion": "", "genero": "bebé"}
                        ]
                    }
                ]
            },
            {
                "nombre": "Disfraces y trajes especiales",
                "descripcion": "",
                "genero": "",
            },
            {
                "nombre": "Otras prendas",
                "descripcion": "",
                "genero": "",
            }
        ]
    },
    {
        "nombre": "Calzado",
        "descripcion": "Zapatos y zapatillas",
        "genero": "",
        "hijos": [
            {
                "nombre": "Mujer", "genero": "mujer", "hijos": [
                    {"nombre": "Zapatillas y deportivas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Botas altas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Botines", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Zapatos de tacón", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Zapatos planos / Bailarinas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Sandalias", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Botas de agua", "descripcion": "", "genero": "mujer"}
                ]
            },
            {
                "nombre": "Hombre", "genero": "hombre", "hijos": [
                    {"nombre": "Zapatillas y deportivas", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Botas y botines", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Zapatos formales / Oxford", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Mocasines y Náuticos", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Sandalias y chanclas", "descripcion": "", "genero": "hombre"}
                ]
            },
            {
                "nombre": "Niña", "genero": "niña", "hijos": [
                    {"nombre": "Zapatillas y deportivas niña", "descripcion": "", "genero": "niña"},
                    {"nombre": "Botas y botines niña", "descripcion": "", "genero": "niña"},
                    {"nombre": "Bailarinas y manoletinas", "descripcion": "", "genero": "niña"},
                    {"nombre": "Sandalias niña", "descripcion": "", "genero": "niña"},
                    {"nombre": "Zapatos colegiales niña", "descripcion": "", "genero": "niña"}
                ]
            },
            {
                "nombre": "Niño", "genero": "niño", "hijos": [
                    {"nombre": "Zapatillas y deportivas niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Botas y botines niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Zapatos de vestir niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Sandalias niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Zapatos colegiales niño", "descripcion": "", "genero": "niño"}
                ]
            },
            {
                "nombre": "Bebé", "genero": "bebé", "hijos": [
                    {"nombre": "Patucos", "descripcion": "Para recién nacidos", "genero": "bebé"},
                    {"nombre": "Badanas y sin suela", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Zapatos primeros pasos", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Deportivas bebé", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Botitas bebé", "descripcion": "", "genero": "bebé"}
                ]
            }
        ]
    },
    {
        "nombre": "Bolsos",
        "descripcion": "Bolsos, mochilas y maletas",
        "genero": "",
        "hijos":[
            {"nombre": "Mochilas", "descripcion": "", "genero": ""},
            {"nombre": "Bolsas de playa", "descripcion": "", "genero": "mujer"},
            {"nombre": "Maletines", "descripcion": "", "genero": ""},
            {"nombre": "Bolsos cubo", "descripcion": "", "genero": "mujer"},
            {"nombre": "Riñoneras", "descripcion": "", "genero": ""},
            {"nombre": "Bolsos de fiesta", "descripcion": "", "genero": "mujer"},
            {"nombre": "Portatrajes", "descripcion": "", "genero": ""},
            {"nombre": "Bolsas de deporte", "descripcion": "", "genero": ""},
            {"nombre": "Bolsos de mano", "descripcion": "", "genero": "mujer"},
            {"nombre": "Bolsos boho", "descripcion": "", "genero": "mujer"},
            {"nombre": "Bolsas de viaje", "descripcion": "", "genero": ""},
            {"nombre": "Maletas", "descripcion": "", "genero": ""},
            {"nombre": "Neceseres", "descripcion": "", "genero": ""},
            {"nombre": "Satchels", "descripcion": "", "genero": "mujer"},
            {"nombre": "Bolsos de hombro", "descripcion": "", "genero": "mujer"},
            {"nombre": "Bolsos tote", "descripcion": "", "genero": "mujer"},
            {"nombre": "Monederos y carteras", "descripcion": "", "genero": ""},
        ]
    },
    {
        "nombre": "Accesorios",
        "descripcion": "Complementos de moda",
        "genero": "",
        "hijos": [
            {
                "nombre": "Mujer", "genero": "mujer", "hijos": [
                    {
                        "nombre": "Joyeria", 
                        "descripcion": "Collares, anillos, pulseras", 
                        "genero": "mujer",
                        "hijos": [
                            {"nombre": "Anillos", "descripcion": "Anillos y sortijas", "genero": "mujer"},
                            {"nombre": "Pendientes", "descripcion": "Aros, largos, botón", "genero": "mujer"},
                            {"nombre": "Collares y colgantes", "descripcion": "Gargantillas, cadenas", "genero": "mujer"},
                            {"nombre": "Pulseras y brazaletes", "descripcion": "Esclavas, pulseras de cadena", "genero": "mujer"},
                            {"nombre": "Tobilleras", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Broches", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Conjuntos de joyería", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {"nombre": "Bandanas y pañuelos para el pelo", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Cinturones", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Sombreros y gorros", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Gafas de sol", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bufandas y pañuelos", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Accesorios de cabello", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Relojes", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Guantes", "descripcion": "", "genero": "mujer"}
                ]
            },
            {
                "nombre": "Hombre", "genero": "hombre", "hijos": [
                    {
                        "nombre": "Joyeria", 
                        "descripcion": "Pulseras, anillos, gemelos", 
                        "genero": "hombre",
                        "hijos": [
                            {"nombre": "Anillos y sellos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pulseras", "descripcion": "De cuero, acero, plata", "genero": "hombre"},
                            {"nombre": "Collares y cadenas", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pendientes", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Gemelos", "descripcion": "Para camisas", "genero": "hombre"},
                            {"nombre": "Pasadores de corbata", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {"nombre": "Cinturones", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Sombreros y gorras", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Gafas de sol", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Bufandas", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Corbatas y pajaritas", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Relojes", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Guantes", "descripcion": "", "genero": "hombre"},
                ]
            },
            {
                "nombre": "Niña", 
                "genero": "niña", 
                "hijos": [
                    {
                        "nombre": "Accesorios para el pelo", 
                        "descripcion": "Adornos para el cabello", 
                        "genero": "niña",
                        "hijos": [
                            {"nombre": "Diademas", "genero": "niña"},
                            {"nombre": "Lazos y moñas", "genero": "niña"},
                            {"nombre": "Horquillas y clips", "genero": "niña"},
                            {"nombre": "Coleteros y elásticos", "genero": "niña"},
                            {"nombre": "Coronas de flores", "genero": "niña"}
                        ]
                    },
                    {
                        "nombre": "Bisutería Infantil", 
                        "descripcion": "Joyas para niñas", 
                        "genero": "niña",
                        "hijos": [
                            {"nombre": "Collares", "genero": "niña"},
                            {"nombre": "Pulseras", "genero": "niña"},
                            {"nombre": "Anillos infantiles", "genero": "niña"},
                            {"nombre": "Pendientes / Arracadas", "genero": "niña"}
                        ]
                    },
                    {"nombre": "Bufandas, guantes y orejeras", "descripcion": "", "genero": "niña"},
                    {"nombre": "Gorros y sombreros", "descripcion": "", "genero": "niña"},
                    {"nombre": "Gafas de sol", "descripcion": "", "genero": "niña"},
                    {"nombre": "Cinturones", "descripcion": "", "genero": "niña"},
                    {"nombre": "Mochilas y bolsos", "descripcion": "Mochilas escolares y bolsitos", "genero": "niña"},
                    {"nombre": "Relojes infantiles", "descripcion": "", "genero": "niña"},
                    {"nombre": "Paraguas e impermeables", "descripcion": "", "genero": "niña"}
                ]
            },
            {
                "nombre": "Niño", "genero": "niño", "hijos": [
                    {"nombre": "Gorras y sombreros niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Cinturones niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Bufandas y guantes niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Mochilas infantiles niño", "descripcion": "", "genero": "niño"}
                ]
            },
            {
                "nombre": "Bebé", "genero": "bebé", "hijos": [
                    {"nombre": "Baberos y bandanas", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Muselinas y gasas", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Arrullos y mantas", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Gorritos bebé", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Manoplas antiarañazos", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Lazos y diademas bebé", "descripcion": "", "genero": "bebé"}
                ]
            },
            {
                "nombre": "Unisex / Otros", "genero": "", "hijos": [
                    {"nombre": "Paraguas", "descripcion": "", "genero": ""},
                    {"nombre": "Llaveros", "descripcion": "", "genero": ""},
                ]
            }
        ]
    }
]

# ==============================================================================
# 2. LÓGICA DE SINCRONIZACIÓN (OPTIMIZADA)
# ==============================================================================

def sincronizar_atributos(db: Session, categoria_id: int, nombre_categoria: str, tipo_raiz: str, ruta_nombres: list, mapa_atributos: dict):
    nombre = nombre_categoria.lower()
    ruta_str = " > ".join(ruta_nombres).lower()
    tipo_seguro = tipo_raiz.lower().strip() if tipo_raiz else ""
    
    plantilla = [{"nombre": "peso_kg", "tipo": "number", "opciones": None}]

    MATERIALES_ROPA = ["Algodón", "Algodón Orgánico", "Lino", "Seda", "Lana", "Lana Merino", "Cachemira (Cashmere)", "Mohair", "Angora", "Alpaca", "Denim / Vaquero", "Cuero / Piel", "Ante / Serraje", "Pana", "Terciopelo", "Tweed", "Gasa / Chifón", "Encaje", "Viscosa / Rayón", "Tencel / Lyocell", "Poliéster", "Nylon", "Elastano / Spandex", "Mezcla de materiales", "Otro"]
    MATERIALES_CALZADO = ["Algodón", "Cuero liso", "Cuero vegano / Sintético", "Ante / Serraje", "Charol", "Lona / Canvas", "Malla / Textil transpirable", "Goma / Caucho", "Satén / Seda", "Corcho", "Otro"]
    MATERIALES_BOLSOS = ["Cuero auténtico", "Cuero vegano / Sintético", "Lona / Canvas", "Nylon", "Rafia / Paja", "Ante / Serraje", "Terciopelo", "Charol", "Algodón", "Otro"]

    if tipo_seguro == "ropa":
        es_inferior = any(p in ruta_str for p in ["pantal", "vaquero", "jean", "short", "leggin", "bermuda", "chino", "capri", "jogger", "pitillo", "harén", "cargo", "polaina", "cubrepañal", "boyfriend", "campana", "skinny", "straight", "relaxed"])
        es_falda = any(p in ruta_str for p in ["fald", "minifalda"])
        es_cuerpo_entero = any(p in ruta_str for p in ["vestido", "mono", "peto", "pelele", "ranita", "buzo", "enterizo", "maxi", "playero"])
        es_interior_bano_pijama = any(p in ruta_str for p in ["calcetin", "media", "pijama", "bata", "bañador", "bikini", "sujetador", "calzoncillo", "slip", "boxer", "braguita", "culetin", "lencería", "saco de dormir", "babero", "muselina", "arrullo", "albornoz", "trikini", "pareo", "caftan", "leotardo", "posparto", "pañal", "baño", "interior"])
        es_conjunto_traje = any(p in ruta_str for p in ["conjunto", "traje", "chándal", "disfraz", "esmoquin"])
        es_superior_sin_mangas = any(p in ruta_str for p in ["sin manga", "chaleco", "crop top", "tirante", "halter", "descubiert", "poncho", "top", "bandana"])
        es_superior_con_mangas = any(p in ruta_str for p in ["camis", "blusa", "túnica", "body", "bodies", "peplum", "polo", "henley", "abrigo", "trenca", "sobretodo", "parka", "chaquet", "impermeable", "gabardina", "cazadora", "bomber", "polar", "harrington", "pluma", "plumífero", "sobrecamisa", "cortaviento", "sudadera", "jers", "kimono", "cárdigan", "bolero", "blazer", "americana", "chubasquero"])

        if es_inferior:
            plantilla.extend([
                {"nombre": "color", "tipo": "color-dropdown", "opciones": None},
                {"nombre": "talla", "tipo": "select", "opciones": [str(i) for i in range(32, 55)] + ["S", "M", "L", "XL"]},
                {"nombre": "cintura_cm", "tipo": "number", "opciones": None},
                {"nombre": "cadera_cm", "tipo": "number", "opciones": None},
                {"nombre": "tiro_cm", "tipo": "number", "opciones": None},
                {"nombre": "largo_entrepierna_cm", "tipo": "number", "opciones": None},
                {"nombre": "ancho_bajo_cm", "tipo": "number", "opciones": None},
                {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}
            ])
        elif es_falda:
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": ["XXS", "XS", "S", "M", "L", "XL", "XXL"]}, {"nombre": "cintura_cm", "tipo": "number", "opciones": None}, {"nombre": "cadera_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}])
        elif es_cuerpo_entero:
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": ["XXS", "XS", "S", "M", "L", "XL", "XXL"]}, {"nombre": "sisa_a_sisa_cm", "tipo": "number", "opciones": None}, {"nombre": "cintura_cm", "tipo": "number", "opciones": None}, {"nombre": "cadera_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}])
        elif es_interior_bano_pijama:
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": ["XS", "S", "M", "L", "XL", "Única"]}, {"nombre": "cintura_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}])
        elif es_conjunto_traje:
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": ["XXS", "XS", "S", "M", "L", "XL", "XXL", "Única"]}, {"nombre": "sisa_a_sisa_cm", "tipo": "number", "opciones": None}, {"nombre": "cintura_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}])
        elif es_superior_sin_mangas:
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": ["XXS", "XS", "S", "M", "L", "XL", "XXL", "Única"]}, {"nombre": "sisa_a_sisa_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}])
        elif es_superior_con_mangas:
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": ["XXS", "XS", "S", "M", "L", "XL", "XXL", "Única"]}, {"nombre": "sisa_a_sisa_cm", "tipo": "number", "opciones": None}, {"nombre": "hombros_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_manga_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}])
        else:
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": [str(i) for i in range(32, 55)] + ["XXS", "XS", "S", "M", "L", "XL", "XXL", "Única"]}, {"nombre": "sisa_a_sisa_cm", "tipo": "number", "opciones": None}, {"nombre": "hombros_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_manga_cm", "tipo": "number", "opciones": None}, {"nombre": "cintura_cm", "tipo": "number", "opciones": None}, {"nombre": "cadera_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}])

    elif tipo_seguro == "calzado":
        plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": [str(i) for i in range(15, 48)]}, {"nombre": "longitud_plantilla_cm", "tipo": "number", "opciones": None}, {"nombre": "tacon_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_CALZADO}])

    elif tipo_seguro == "bolsos":
        plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "ancho_cm", "tipo": "number", "opciones": None}, {"nombre": "alto_cm", "tipo": "number", "opciones": None}, {"nombre": "profundidad_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_correa_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_BOLSOS}])
        
    elif tipo_seguro == "accesorios":
        PLANTILLA_JOYERIA_BASE = [{"nombre": "material_joyeria", "tipo": "select", "opciones": ["Oro Amarillo", "Oro Blanco", "Oro Rosa", "Plata", "Platino", "Acero Inoxidable", "Bisutería", "Otro"]}, {"nombre": "pureza_metal", "tipo": "select", "opciones": ["9K", "14K", "18K", "22K", "24K", "Plata 925", "No aplica"]}, {"nombre": "piedra", "tipo": "text", "opciones": None}, {"nombre": "color_piedra", "tipo": "color-dropdown", "opciones": None}, {"nombre": "quilates_piedra_ct", "tipo": "number", "opciones": None}]
        
        if any(p in ruta_str for p in ["anillo", "sello"]):
            plantilla.extend([{"nombre": "talla_anillo", "tipo": "text", "opciones": None}] + PLANTILLA_JOYERIA_BASE)
        elif any(p in ruta_str for p in ["collar", "cadena", "gargantilla", "pulsera", "brazalete", "tobillera", "esclava"]):
            plantilla.extend([{"nombre": "longitud_cm", "tipo": "number", "opciones": None}] + PLANTILLA_JOYERIA_BASE)
        elif any(p in ruta_str for p in ["pendient", "arracada", "broche", "gemelo", "pasador"]):
            plantilla.extend(PLANTILLA_JOYERIA_BASE)
        elif any(p in ruta_str for p in ["cinturon", "cinturones"]):
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": ["XS", "S", "M", "L", "XL", "Única"]}, {"nombre": "longitud_cm", "tipo": "number", "opciones": None}, {"nombre": "ancho_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_BOLSOS}])
        elif any(p in ruta_str for p in ["sombrero", "gorro", "gorra"]):
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": ["XS", "S", "M", "L", "XL", "Única"]}, {"nombre": "circunferencia_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}])
        elif any(p in ruta_str for p in ["gafa"]):
            plantilla.extend([{"nombre": "color_montura", "tipo": "color-dropdown", "opciones": None}, {"nombre": "color_lente", "tipo": "color-dropdown", "opciones": None}, {"nombre": "material_montura", "tipo": "select", "opciones": ["Pasta / Plástico", "Metal", "Acetato", "Mixto", "Otro"]}, {"nombre": "proteccion_uv", "tipo": "text", "opciones": None}])
        elif any(p in ruta_str for p in ["reloj"]):
            plantilla.extend([{"nombre": "color_esfera", "tipo": "color-dropdown", "opciones": None}, {"nombre": "color_correa", "tipo": "color-dropdown", "opciones": None}, {"nombre": "material_correa", "tipo": "select", "opciones": ["Acero", "Cuero", "Caucho / Silicona", "Tela / Nylon", "Otro"]}, {"nombre": "diametro_esfera_mm", "tipo": "number", "opciones": None}])
        elif any(p in ruta_str for p in ["bufanda", "pañuelo", "bandana", "pajarita", "corbata"]):
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "longitud_cm", "tipo": "number", "opciones": None}, {"nombre": "ancho_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA}])
        else:
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": ["XS", "S", "M", "L", "XL", "Única"]}, {"nombre": "material", "tipo": "text", "opciones": None}, {"nombre": "dimensiones_notas", "tipo": "text", "opciones": None}])

    actuales = mapa_atributos.get(categoria_id, {})
    nombres_en_plantilla = set() 
    
    for attr in plantilla:
        nombres_en_plantilla.add(attr["nombre"])
        if attr["nombre"] not in actuales:
            nuevo_attr = AtributoCategoria(
                categoria_id=categoria_id,
                nombre=attr["nombre"],
                tipo=attr["tipo"],
                opciones=attr["opciones"] 
            )
            db.add(nuevo_attr)
            actuales[attr["nombre"]] = nuevo_attr  
        else:
            attr_existente = actuales[attr["nombre"]]
            if attr_existente.opciones != attr["opciones"] or attr_existente.tipo != attr["tipo"]:
                attr_existente.opciones = attr["opciones"]
                attr_existente.tipo = attr["tipo"]

    for nombre_db, attr_db in list(actuales.items()):
        if nombre_db not in nombres_en_plantilla:
            try:
                db.begin_nested() 
                db.delete(attr_db)
                db.flush()
                del actuales[nombre_db] 
            except IntegrityError:
                db.rollback()

def sincronizar_recursivo(db: Session, nodo: dict, mapa_categorias: dict, mapa_atributos: dict, parent_id: int = None, tipo_raiz: str = None, ruta_nombres: list = None):
    if ruta_nombres is None: ruta_nombres = []
        
    nombre = nodo["nombre"]
    if nombre.lower() == "todos": return

    if parent_id is None: tipo_raiz = nombre

    ruta_actual = ruta_nombres + [nombre.lower()]
    genero_valor = nodo.get("genero") or None 

    clave_cache = (nombre, parent_id)
    categoria = mapa_categorias.get(clave_cache)

    if categoria:
        if categoria.genero != genero_valor or categoria.descripcion != nodo.get("descripcion", ""):
            categoria.genero = genero_valor
            categoria.descripcion = nodo.get("descripcion", "")
            categoria.activo = True 
    else:
        categoria = Categoria(
            nombre=nombre,
            descripcion=nodo.get("descripcion", ""),
            genero=genero_valor,
            parent_id=parent_id,
            activo=True 
        )
        print(f"⏳ Agregando categoría: {nombre} a la sesión...")
        db.add(categoria)
        
        # Este es el punto crítico donde muere la conexión
        print(f"🔥 Ejecutando db.flush() para que Clever Cloud asigne el ID a: {nombre}...")
        db.flush() 
        print(f"✅ Flush exitoso. ID asignado: {categoria.id}")
        
        mapa_categorias[clave_cache] = categoria 

    sincronizar_atributos(db, categoria.id, nombre, tipo_raiz, ruta_actual, mapa_atributos)

    for hijo in nodo.get("hijos", []):
        sincronizar_recursivo(db, hijo, mapa_categorias, mapa_atributos, parent_id=categoria.id, tipo_raiz=tipo_raiz, ruta_nombres=ruta_actual)

# ==============================================================================
# 3. BLOQUE DE EJECUCIÓN 
# ==============================================================================
def poblar_categorias():
    db = SessionLocal()
    try:
        print("🚀 Iniciando lectura inicial de la base de datos...")
        
        todas_categorias = db.query(Categoria).all()
        mapa_categorias = {(c.nombre, c.parent_id): c for c in todas_categorias}

        todos_atributos = db.query(AtributoCategoria).all()
        mapa_atributos = {}
        for a in todos_atributos:
            if a.categoria_id not in mapa_atributos:
                mapa_atributos[a.categoria_id] = {}
            mapa_atributos[a.categoria_id][a.nombre] = a
        
        print("📥 Lectura finalizada. Empezando sincronización...")
        for cat in categorias_master:
            sincronizar_recursivo(db, cat, mapa_categorias, mapa_atributos)
            
        print("💾 Enviando commit final (guardado definitivo)...")
        db.commit()
        print("✅ Categorías y Atributos actualizados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la sincronización: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    print("1. Arrancando script con LOGS de SQLAlchemy ACTIVADOS...")
    try:
        print("2. Intentando conectar y crear tablas (create_all)...")
        Base.metadata.create_all(bind=engine)
        print("3. Tablas verificadas con éxito.")
    except Exception as e:
        print(f"❌ Error crítico de conexión al arrancar: {e}")
        sys.exit(1)

    print("4. Llamando a la función principal...")
    poblar_categorias()