from pymysql import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base

# Importar modelos
from app.models.categorias_model import Categoria
from app.models.clientes_model import Cliente
from app.models.producto_model import Producto
from app.models.marcas_model import Marca
from app.models.variantes_model import Variante
from app.models.variante_imagen_model import Imagen
from app.models.ventas_model import Venta
from app.models.atributo_model import Atributo, ValorAtributo
from app.models.lotes_model import StockConfig, StockUnit
from app.models.proveedores_model import Proveedor
from app.models.pagos_consignacion_model import PagoConsignacion
from app.models.gastos_model import Gasto
from app.models.atributo_categoria_model import AtributoCategoria

# ==============================================================================
# 1. DATOS MAESTROS (Estructura: Categoría -> Género -> Tipo de Prenda)
# ==============================================================================
categorias_master = [
    {
        "nombre": "Mujer",
        "descripcion": "Todo para mujer",
        "genero": "mujer",
        "hijos": [
            {
                "nombre": "Ropa",
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
                            {"nombre": "Pantalones pitillos", "descripcion": "", "genero": "mujer"},
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
                            {"nombre": "De cuero", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Estilo cargo", "descripcion": "", "genero": "mujer"},
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
                                    {"nombre": "Abrigos de piel sintética", "genero": "mujer"},
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
                                    {"nombre": "Otras chaquetas", "genero": "mujer"},
                                ]
                            },
                            {"nombre": "Capas y ponchos", "genero": "mujer"},
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
                            {"nombre": "Chalecos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Otros jerséis u sudaderas", "genero": "mujer"},
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
                            {"nombre": "Piezas de traje", "genero": "mujer"},
                            {"nombre": "Otros trajes y blazers", "genero": "mujer"},
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
                            {"nombre": "Otros", "genero": "mujer"},
                        ]
                    },
                    {
                        "nombre": "Lencería y pijamas",
                        "descripcion": "",
                        "genero": "mujer", 
                        "hijos": [
                            {"nombre": "Sujetadores", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Braguitas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Conjuntos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Lencería moldeadora", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pijamas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Batas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Medias", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Calcetines", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Accesorios de lencería", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Otros", "genero": "mujer"},
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
                                    {"nombre": "Ropa interior", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Pijamas", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Sujetadores premama y posparto", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Otros", "genero": "mujer"},
                                ]
                            },
                            {"nombre": "Ropa de deporte", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Otros", "genero": "mujer"},
                        ]
                    },

                    {
                        "nombre": "Ropa deportiva",
                        "descripcion": "",
                        "genero": "mujer", 
                        "hijos": [
                            {"nombre": "Ropa de abrigo", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Chándales", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Pantalones", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Shorts", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Vestidos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Faldas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Tops y camisetas deportivas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Camisetas de equipos", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Sudaderas", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Accesorios", 
                             "descripcion": "", 
                             "genero": "mujer",
                             "hijos":[
                                    {"nombre": "Gafas", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Guantes", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Gorras", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Bufandas", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Muñequeras", "descripcion": "", "genero": "mujer"},
                                    {"nombre": "Otros", "descripcion": "", "genero": "mujer"},
                             ]},
                            {"nombre": "Sujetadores", "descripcion": "", "genero": "mujer"},
                            {"nombre": "Otros", "descripcion": "", "genero": "mujer"},
                        ]
                    },
                    {"nombre": "Disfraces y trajes especiales", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Otras prendas", "descripcion": "", "genero": "mujer"},
                ]
            },
            {
                "nombre": "Calzado",
                "descripcion": "Zapatos y zapatillas para mujer",
                "genero": "mujer",
                "hijos": [
                    {"nombre": "Bailarinas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Naúticas y mocasines", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Botas", 
                     "descripcion": "", 
                     "genero": "mujer",
                     "hijos":[
                         {"nombre": "Botines", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Botas de media pantorrilla", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Botas altas", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Botas por encia de la rodilla", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Botas de nieve", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Botas de agua", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Calzado de seguridad", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Otras botas", "descripcion": "", "genero": "mujer"}
                     ]},
                    {"nombre": "Zuecos y mules", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Alpargatas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Chanclas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Tacones", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Zapatos con cordones", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Merceditas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Sandalias", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Pantunflas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Zapatillas de deporte", 
                     "descripcion": "", 
                     "genero": "mujer",
                     "hijos":[
                         {"nombre": "Zapatillas de baloncesto", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Pies de gato", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Zapatillas de ciclismo", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Zapatos de baile", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Botas de fútbol", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Zapatos de golf", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Calzado y botas de montaña", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Patines de hielo", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Zapatilla de fútbol sala", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Para gimnasio", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Botas de moto", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Patines de ruedas", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Zapatillas de correr", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Botas de esquí", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Botas de snowboard", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Calzado para nadar y agua", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Zapatillas de tenis", "descripcion": "", "genero": "mujer"},
                         {"nombre": "Otros", "descripcion": "", "genero": "mujer"},
                     ]},
                    {"nombre": "Zapatillas", "descripcion": "", "genero": "mujer"},
                ]
            },
            {
                "nombre": "Bolsos",
                "descripcion": "Bolsos para mujer",
                "genero": "mujer",
                "hijos": [
                    {"nombre": "Mochilas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsas de playa", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Maletines", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsos cubo", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Riñoneras", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsos de fiesta", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Portatrajes", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsa de deporte, bolso de deporte, bolsa de gimnasio", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsos de mano", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsos boho", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsas de viaje", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Maletas", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Neceseres", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Satchels", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsos de hombro", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsos tote", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Monederos y carteras", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Bolsos de pulsera", "descripcion": "", "genero": "mujer"},
                    {"nombre": "Otros", "descripcion": "", "genero": "mujer"},
                ]
            },
            {
                "nombre": "Accesorios",
                "descripcion": "Complementos de moda para mujer",
                "genero": "mujer",
                "hijos": [
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
                    {
                        "nombre": "Relojes",
                        "descripcion": "Relojes de pulsera y accesorios",
                        "genero": "mujer",
                        "hijos": [
                            {
                                "nombre": "Relojes analógicos",
                                "descripcion": "Modelos clásicos con movimiento de manecillas",
                                "genero": "mujer"
                            },
                            {
                                "nombre": "Relojes digitales",
                                "descripcion": "Relojes con pantalla numérica y funciones electrónicas",
                                "genero": "mujer"
                            },
                            {
                                "nombre": "Smartwatches",
                                "descripcion": "Relojes inteligentes y monitores de actividad",
                                "genero": "mujer"
                            },
                            {
                                "nombre": "Relojes deportivos",
                                "descripcion": "Modelos resistentes al agua con cronómetro",
                                "genero": "mujer"
                            },
                            {
                                "nombre": "Correas y accesorios",
                                "descripcion": "Correas de repuesto, estuches y herramientas",
                                "genero": "mujer"
                            }
                        ]
                    }
                ]
            }
        ]
    },
    {
        "nombre": "Hombre",
        "descripcion": "Todo para hombre",
        "genero": "hombre",
        "hijos": [
            {
                "nombre": "Ropa",
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
                                    {"nombre": "Otras camisas", "descripcion": "", "genero": "hombre"},
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
                                    {"nombre": "Otras camisetas", "descripcion": "", "genero": "hombre"},
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
                            {"nombre": "Capri", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pantalones de pinzas / Vestir", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pantalones anchos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Otros pantalones", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Shorts",
                        "descripcion": "",
                        "genero": "hombre", 
                        "hijos": [
                            {"nombre": "Estilo cargo", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Chinos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Vaqueros", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Bermudas chinas", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Shorts de chándal", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Otros shorts", "descripcion": "", "genero": "hombre"},
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
                                    {"nombre": "Sobretodos y abrigos largos", "genero": "hombre"},
                                    {"nombre": "Parkas", "genero": "hombre"},
                                    {"nombre": "Chaquetones marineros", "genero": "hombre"},
                                    {"nombre": "Impermeables", "genero": "hombre"},
                                    {"nombre": "Gabardinas", "descripcion": "", "genero": "hombre"},
                                ]
                            },
                            {"nombre": "Chalecos acolchados", "genero": "hombre"},
                            {
                                "nombre": "Chaquetas",
                                "genero": "hombre",
                                "hijos": [
                                    {"nombre": "Cazadoras biker", "genero": "hombre"},
                                    {"nombre": "Chaquetas bombers", "genero": "hombre"},
                                    {"nombre": "Cazadoras vaqueras", "genero": "hombre"},
                                    {"nombre": "Chaquetas militares y utilitarias", "genero": "hombre"},
                                    {"nombre": "Forros polares", "genero": "hombre"},
                                    {"nombre": "Chaquetas harrington", "genero": "hombre"},
                                    {"nombre": "Chaquetas de plumas", "genero": "hombre"},
                                    {"nombre": "Chaquetas acolchadas", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Sobrecamisas", "genero": "hombre"},
                                    {"nombre": "Chaquetas de esquí y snow", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Chaquetas universitarias", "descripcion": "", "genero": "hombre"},
                                    {"nombre": "Cortavientos", "genero": "hombre"},
                                    {"nombre": "Otras chaquetas", "descripcion": "", "genero": "hombre"},
                                ]
                            },
                            {"nombre": "Ponchos", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Jerséis y sudaderas",
                        "descripcion": "",
                        "genero": "hombre",
                        "hijos": [
                            {"nombre": "Jerséis", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Sudaderas con capucha", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Sudaderas sin capucha", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Sudaderas con cremallera", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Cárdigans", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Cuello redondo", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Cuello pico", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Cuello alto", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Largos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "De punto", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Chalecos", "descripcion": "", "genero": "hombre"},
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
                            {"nombre": "Otros", "descripcion": "", "genero": "hombre"},
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
                            {"nombre": "Albornoces", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Otrso", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Pijamas",
                        "descripcion": "",
                        "genero": "hombre", 
                        "hijos": [
                            {"nombre": "Pijamas de una pieza", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pantalones de pijama", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pijamas completos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Camisetas de pijama", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {
                        "nombre": "Bañadores",
                        "descripcion": "",
                        "genero": "hombre"
                    },
                    {
                        "nombre": "Ropa y accesorios deportivos",
                        "descripcion": "",
                        "genero": "hombre", 
                        "hijos": [
                            {"nombre": "Ropa de abrigo", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Ropa de entrenamiento", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pantalones", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Shorts", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Camisetas y tops", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Camisetas de equipos", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Sudaderas y suéteres", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Accesorios", 
                             "descripcion": "", 
                             "genero": "hombre", 
                             "hijos":[
                                {"nombre": "Gafas", "descripcion": "", "genero": "hombre"},
                                {"nombre": "Guantes", "descripcion": "", "genero": "hombre"},
                                {"nombre": "Gorras", "descripcion": "", "genero": "hombre"},
                                {"nombre": "Bufandas", "descripcion": "", "genero": "hombre"},
                                {"nombre": "Muñequeras", "descripcion": "", "genero": "hombre"},
                                {"nombre": "Otros", "descripcion": "", "genero": "hombre"},
                            ]},
                            {"nombre": "Otros", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {"nombre": "Disfraces y trajes especiales", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Otras prendas", "descripcion": "", "genero": "hombre"},
                ]
            },
            {
                "nombre": "Calzado",
                "descripcion": "Zapatos y zapatillas para hombre",
                "genero": "hombre",
                "hijos": [
                    {"nombre": "Naúticos y mocasines", "descripcion": "", "genero": "hombre"},
                    {
                      "nombre": "Botas",
                      "descripcion": "", 
                      "genero": "hombre",
                      "hijos":[
                            {"nombre": "Botas chelsea y sin cordones", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Botas desert y con cordones", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Botas de nieve", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Botas de agua", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Calzado de seguridad", "descripcion": "", "genero": "hombre"},
                      ]
                    },
                    {"nombre": "Zuecos y mules", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Alpargatas", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Chanclas", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Zapatos de vestir", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Sandalias", "descripcion": "", "genero": "hombre"},
                    {"nombre": "Pantuflas", "descripcion": "", "genero": "hombre"},
                    {
                        "nombre": "Zapatillas de deporte", 
                        "descripcion": "", 
                        "genero": "hombre",
                        "hijos":[
                            {"nombre": "Zapatillas de baloncesto", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Pies de gato", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Zapatillas de ciclismo", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Zapatos de baile", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Botas de fútbol", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Zapatos de golf", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Calzado y botas de montaña", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Patines de hielo", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Zapatillas de fútbol sala", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Para gimnasio", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Botas de moto", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Patines de ruedas", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Zapatilla de correr", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Botas de esquí", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Botas de snowboard", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Calzado para nadar y agua", "descripcion": "", "genero": "hombre"},
                            {"nombre": "Zapatillas de tenis", "descripcion": "", "genero": "hombre"},
                        ]
                    },
                    {"nombre": "Zapatillas", "descripcion": "", "genero": "hombre"}
                    
                ]
            },
            {
                "nombre": "Accesorios",
                "descripcion": "Complementos de moda para hombre",
                "genero": "hombre",
                "hijos": [
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
                    {
                        "nombre": "Relojes",
                        "descripcion": "Relojes de pulsera y accesorios para caballero",
                        "genero": "hombre",
                        "hijos": [
                            {
                                "nombre": "Relojes analógicos",
                                "descripcion": "Modelos clásicos de cuarzo con manecillas",
                                "genero": "hombre"
                            },
                            {
                                "nombre": "Relojes automáticos",
                                "descripcion": "Relojes de movimiento mecánico",
                                "genero": "hombre"
                            },
                            {
                                "nombre": "Relojes digitales",
                                "descripcion": "Modelos con pantalla LCD y funciones electrónicas",
                                "genero": "hombre"
                            },
                            {
                                "nombre": "Smartwatches",
                                "descripcion": "Relojes inteligentes y deportivos",
                                "genero": "hombre"
                            },
                            {
                                "nombre": "Relojes deportivos y cronógrafos",
                                "descripcion": "Modelos de alta resistencia y cronometría",
                                "genero": "hombre"
                            },
                            {
                                "nombre": "Correas y accesorios",
                                "descripcion": "Correas de cuero, acero, silicona y estuches",
                                "genero": "hombre"
                            }
                        ]
                    }
                ]
            }
        ]
    },
    {
        "nombre": "Niñas",
        "descripcion": "Todo para niñas",
        "genero": "niña",
        "hijos": [
            {
                "nombre": "Ropa",
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
                "nombre": "Calzado",
                "descripcion": "Zapatos para niña",
                "genero": "niña",
                "hijos": [
                    {"nombre": "Zapatillas y deportivas niña", "descripcion": "", "genero": "niña"},
                    {"nombre": "Botas y botines niña", "descripcion": "", "genero": "niña"},
                    {"nombre": "Bailarinas y manoletinas", "descripcion": "", "genero": "niña"},
                    {"nombre": "Sandalias niña", "descripcion": "", "genero": "niña"},
                    {"nombre": "Zapatos colegiales niña", "descripcion": "", "genero": "niña"}
                ]
            },
            {
                "nombre": "Accesorios",
                "descripcion": "Complementos para niña",
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
                    {"nombre": "Relojes infantiles", "descripcion": "", "genero": "niña"},
                ]
            }
        ]
    },
    {
        "nombre": "Niños",
        "descripcion": "Todo para niños",
        "genero": "niño",
        "hijos": [
            {
                "nombre": "Ropa",
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
                "nombre": "Calzado",
                "descripcion": "Zapatos para niño",
                "genero": "niño",
                "hijos": [
                    {"nombre": "Zapatillas y deportivas niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Botas y botines niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Zapatos de vestir niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Sandalias niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Zapatos colegiales niño", "descripcion": "", "genero": "niño"}
                ]
            },
            {
                "nombre": "Accesorios",
                "descripcion": "Complementos para niño",
                "genero": "niño",
                "hijos": [
                    {"nombre": "Gorras y sombreros niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Cinturones niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Bufandas y guantes niño", "descripcion": "", "genero": "niño"},
                    {"nombre": "Mochilas infantiles niño", "descripcion": "", "genero": "niño"}
                ]
            }
        ]
    },
    {
        "nombre": "Bebés",
        "descripcion": "Todo para bebés (0-36 meses)",
        "genero": "bebé",
        "hijos": [
            {
                "nombre": "Ropa",
                "descripcion": "Ropa de bebé",
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
                "nombre": "Calzado",
                "descripcion": "Zapatos para bebé",
                "genero": "bebé",
                "hijos": [
                    {"nombre": "Patucos", "descripcion": "Para recién nacidos", "genero": "bebé"},
                    {"nombre": "Badanas y sin suela", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Zapatos primeros pasos", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Deportivas bebé", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Botitas bebé", "descripcion": "", "genero": "bebé"}
                ]
            },
            {
                "nombre": "Accesorios",
                "descripcion": "Complementos para bebé",
                "genero": "bebé",
                "hijos": [
                    {"nombre": "Baberos y bandanas", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Muselinas y gasas", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Arrullos y mantas", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Gorritos bebé", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Manoplas antiarañazos", "descripcion": "", "genero": "bebé"},
                    {"nombre": "Lazos y diademas bebé", "descripcion": "", "genero": "bebé"}
                ]
            }
        ]
    },
    
]

# ==============================================================================
# 2. LÓGICA DE SINCRONIZACIÓN (OPTIMIZADA CON CACHÉ EN MEMORIA)
# ==============================================================================

def sincronizar_atributos(db: Session, categoria_id: int, nombre_categoria: str, tipo_raiz: str, ruta_nombres: list, mapa_atributos: dict, indent: str = ""):
    ruta_str = " > ".join(ruta_nombres).lower()
    # Limpiamos el tipo_raiz para asegurar que coincida con las condiciones
    tipo_seguro = tipo_raiz.lower().strip() if tipo_raiz else ""
    
    plantilla = [{"nombre": "peso_kg", "tipo": "number", "opciones": None}]

    # --- MATERIALES GLOBALES ---
    MATERIALES_ROPA = ["Algodón", "Algodón Orgánico", "Lino", "Seda", "Lana", "Lana Merino", "Cachemira (Cashmere)", "Mohair", "Angora", "Alpaca", "Denim / Vaquero", "Cuero / Piel", "Ante / Serraje", "Pana", "Terciopelo", "Tweed", "Gasa / Chifón", "Encaje", "Viscosa / Rayón", "Tencel / Lyocell", "Poliéster", "Nylon", "Elastano / Spandex", "Mezcla de materiales", "Otro"]
    MATERIALES_CALZADO = ["Algodón", "Cuero liso", "Cuero vegano / Sintético", "Ante / Serraje", "Charol", "Lona / Canvas", "Malla / Textil transpirable", "Goma / Caucho", "Satén / Seda", "Corcho", "Otro"]
    MATERIALES_BOLSOS = ["Cuero auténtico", "Cuero vegano / Sintético", "Lona / Canvas", "Nylon", "Rafia / Paja", "Ante / Serraje", "Terciopelo", "Charol", "Algodón", "Otro"]
    
    # ✅ 1. TALLAS PARA ROPA GENERAL (Extendida a 9XL)
    TALLAS_ROPA_GENERAL = [
        "30 (XXXS) - UK 2", 
        "32 (XXS) - UK 4", 
        "34 (XS) - UK 6", 
        "36 (S) - UK 8", 
        "38 (M) - UK 10", 
        "40 (L) - UK 12", 
        "42 (XL) - UK 14", 
        "44 (XXL) - UK 16", 
        "46 (3XL) - UK 18", 
        "48 (4XL) - UK 20", 
        "50 (5XL) - UK 22", 
        "52 (6XL) - UK 24", 
        "54 (7XL) - UK 26",
        "56 (8XL) - UK 28",
        "58 (9XL) - UK 30",
        "Única", 
        "Otra talla"
    ]

    # ✅ 2. TALLAS PARA PANTALONES / VAQUEROS (Extendida a 9XL)
    TALLAS_PANTALONES = [
        "W22 (EU 30 / XXXS) - UK 2",
        "W24 (EU 32 / XXS) - UK 4", 
        "W26 (EU 34 / XS) - UK 6", 
        "W28 (EU 36 / S) - UK 8", 
        "W30 (EU 38 / M) - UK 10", 
        "W32 (EU 40 / L) - UK 12",
        "W34 (EU 42 / XL) - UK 14", 
        "W36 (EU 44 / XXL) - UK 16", 
        "W38 (EU 46 / 3XL) - UK 18", 
        "W40 (EU 48 / 4XL) - UK 20", 
        "W42 (EU 50 / 5XL) - UK 22", 
        "W44 (EU 52 / 6XL) - UK 24",
        "W46 (EU 54 / 7XL) - UK 26",
        "W48 (EU 56 / 8XL) - UK 28",
        "W50 (EU 58 / 9XL) - UK 30", 
        "Única", 
        "Otra talla"
    ]

    # ✅ 3. TALLAS BEBÉS (0-36 meses)
    TALLAS_BEBE = [
        "Recién nacido (0 meses)", "0-1 mes (50-56 cm)", "1-3 meses (56-62 cm)", "3-6 meses (62-68 cm)", "6-9 meses (68-74 cm)", "9-12 meses (74-80 cm)", "12-18 meses (80-86 cm)", "18-24 meses (86-92 cm)", "24-36 meses (92-98 cm)", "Única", "Otra talla"
    ]

    # ✅ 4. TALLAS NIÑOS Y NIÑAS (2-16 años)
    TALLAS_NINO = [
        "2-3 años (98 cm)", "3-4 años (104 cm)", "4-5 años (110 cm)", "5-6 años (116 cm)", "6-7 años (122 cm)", "7-8 años (128 cm)", "8-9 años (134 cm)", "9-10 años (140 cm)", "10-11 años (146 cm)", "11-12 años (152 cm)", "12-13 años (158 cm)", "13-14 años (164 cm)", "14-15 años (170 cm)", "15-16 años (176 cm)", "Única", "Otra talla"
    ]

    # ✅ 5. TALLAS COMBINADAS (Para trajes, conjuntos, especial, otras prendas)
    TALLAS_COMBINADAS = [
        # Escala general
        "30 (XXXS) - UK 2", "32 (XXS) - UK 4", "34 (XS) - UK 6", "36 (S) - UK 8", 
        "38 (M) - UK 10", "40 (L) - UK 12", "42 (XL) - UK 14", "44 (XXL) - UK 16", 
        "46 (3XL) - UK 18", "48 (4XL) - UK 20", "50 (5XL) - UK 22", "52 (6XL) - UK 24", 
        "54 (7XL) - UK 26", "56 (8XL) - UK 28", "58 (9XL) - UK 30",
        # Escala de pantalones
        "W22 (EU 30 / XXXS) - UK 2", "W24 (EU 32 / XXS) - UK 4", "W26 (EU 34 / XS) - UK 6", 
        "W28 (EU 36 / S) - UK 8", "W30 (EU 38 / M) - UK 10", "W32 (EU 40 / L) - UK 12", 
        "W34 (EU 42 / XL) - UK 14", "W36 (EU 44 / XXL) - UK 16", "W38 (EU 46 / 3XL) - UK 18", 
        "W40 (EU 48 / 4XL) - UK 20", "W42 (EU 50 / 5XL) - UK 22", "W44 (EU 52 / 6XL) - UK 24",
        "W46 (EU 54 / 7XL) - UK 26", "W48 (EU 56 / 8XL) - UK 28", "W50 (EU 58 / 9XL) - UK 30",
        "Única", "Otra talla"
    ]

    # --- DETECCIÓN DE PÚBLICO ---
    es_bebe = "bebé" in ruta_str or "bebe" in ruta_str
    es_nino_nina = any(x in ruta_str for x in ["niño", "niña", "niños", "niñas"])

    # --- LÓGICA POR DEPARTAMENTO ---
    if tipo_seguro == "ropa":
        es_vestido = "vestido" in ruta_str
        es_conjunto_traje = any(p in ruta_str for p in ["conjunto", "traje", "chándal", "mono", "peto", "pelele"])
        es_superior = any(p in ruta_str for p in ["camiseta", "camisa", "abrigo", "chaqueta", "jers", "sudadera", "top", "blazer", "blusa", "poncho", "bodys", "tops", "chaleco", "buzo"])
        es_falda = "fald" in ruta_str
        es_inferior = any(p in ruta_str for p in ["pantal", "vaquero", "jean", "short", "leggin", "bermuda", "polaina", "ranita", "braguita"])
        es_interior_bano = any(p in ruta_str for p in ["interior", "baño", "bikini", "bañador", "lencería", "pijama", "slip", "sujetador", "body", "calcet", "media", "leotardo"])
        es_especial_o_general = any(p in ruta_str for p in ["disfraz", "disfraces", "especial", "otras prendas", "premama", "premamá", "deporte"])

        # Determinar la lista de tallas según el público y prenda
        if es_bebe:
            lista_tallas = TALLAS_BEBE
        elif es_nino_nina:
            lista_tallas = TALLAS_NINO
        elif es_inferior:
            lista_tallas = TALLAS_PANTALONES
        elif es_conjunto_traje or es_especial_o_general:
            lista_tallas = TALLAS_COMBINADAS
        else:
            lista_tallas = TALLAS_ROPA_GENERAL

        # Aplicar la plantilla según el tipo de prenda (y ocultar medidas para bebés)
        if es_bebe:
            plantilla.extend([
                {"nombre": "color", "tipo": "color-dropdown", "opciones": None}, 
                {"nombre": "talla", "tipo": "select", "opciones": lista_tallas}
            ])
        else:
            if es_vestido:
                plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": lista_tallas}, {"nombre": "hombros_cm", "tipo": "number", "opciones": None}, {"nombre": "sisa_a_sisa_cm", "tipo": "number", "opciones": None}, {"nombre": "cadera_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}])
            elif es_conjunto_traje:
                plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": lista_tallas}, {"nombre": "hombros_cm", "tipo": "number", "opciones": None}, {"nombre": "sisa_a_sisa_cm", "tipo": "number", "opciones": None}, {"nombre": "cintura_cm", "tipo": "number", "opciones": None}, {"nombre": "cadera_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}])
            elif es_superior:
                plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": lista_tallas}, {"nombre": "hombros_cm", "tipo": "number", "opciones": None}, {"nombre": "sisa_a_sisa_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}])
            elif es_falda:
                plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": lista_tallas}, {"nombre": "cintura_cm", "tipo": "number", "opciones": None}, {"nombre": "cadera_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}])
            elif es_inferior:
                plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": lista_tallas}, {"nombre": "cintura_cm", "tipo": "number", "opciones": None}, {"nombre": "cadera_cm", "tipo": "number", "opciones": None}, {"nombre": "tiro_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}])
            elif es_interior_bano:
                plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": lista_tallas}, {"nombre": "cintura_cm", "tipo": "number", "opciones": None}, {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}])
            elif es_especial_o_general:
                plantilla.extend([
                    {"nombre": "color", "tipo": "color-dropdown", "opciones": None},
                    {"nombre": "talla", "tipo": "select", "opciones": lista_tallas},
                    {"nombre": "hombros_cm", "tipo": "number", "opciones": None},
                    {"nombre": "sisa_a_sisa_cm", "tipo": "number", "opciones": None},
                    {"nombre": "cintura_cm", "tipo": "number", "opciones": None},
                    {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}
                ])
            else: # FALLBACK ABSOLUTO
                plantilla.extend([
                    {"nombre": "color", "tipo": "color-dropdown", "opciones": None},
                    {"nombre": "talla", "tipo": "select", "opciones": lista_tallas},
                    {"nombre": "largo_total_cm", "tipo": "number", "opciones": None}
                ])
        
        plantilla.append({"nombre": "material", "tipo": "select", "opciones": MATERIALES_ROPA})

    elif tipo_seguro == "calzado":
        tallas_calzado = [str(i) for i in range(15, 48)] + ["Otra talla"]
        plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": tallas_calzado}, {"nombre": "longitud_plantilla_cm", "tipo": "number", "opciones": None}, {"nombre": "tacon_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_CALZADO}])

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
        elif any(p in ruta_str for p in ["cinturon"]):
            opciones_cinto = TALLAS_NINO if es_nino_nina else ["XS", "S", "M", "L", "XL", "Única", "Otra talla"]
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "talla", "tipo": "select", "opciones": opciones_cinto}, {"nombre": "longitud_cm", "tipo": "number", "opciones": None}, {"nombre": "ancho_cm", "tipo": "number", "opciones": None}, {"nombre": "material", "tipo": "select", "opciones": MATERIALES_BOLSOS}])
        elif any(p in ruta_str for p in ["reloj"]):
            plantilla.extend([{"nombre": "color_esfera", "tipo": "color-dropdown", "opciones": None}, {"nombre": "color_correa", "tipo": "color-dropdown", "opciones": None}, {"nombre": "material_correa", "tipo": "select", "opciones": ["Acero", "Cuero", "Caucho / Silicona", "Tela / Nylon", "Otro"]}, {"nombre": "diametro_esfera_mm", "tipo": "number", "opciones": None}])
        else:
            plantilla.extend([{"nombre": "color", "tipo": "color-dropdown", "opciones": None}, {"nombre": "material", "tipo": "text", "opciones": None}])

    # --- GUARDADO EN BD ---
    actuales = mapa_atributos.get(categoria_id, {})
    nombres_en_plantilla = set() 
    
    for attr in plantilla:
        nombres_en_plantilla.add(attr["nombre"])
        if attr["nombre"] not in actuales:
            nuevo_attr = AtributoCategoria(categoria_id=categoria_id, nombre=attr["nombre"], tipo=attr["tipo"], opciones=attr["opciones"])
            db.add(nuevo_attr)
            print(f"{indent}   ➕ Atributo añadido: {attr['nombre']}")
        else:
            attr_existente = actuales[attr["nombre"]]
            attr_existente.opciones = attr["opciones"]
            attr_existente.tipo = attr["tipo"]

    # --- LIMPIEZA ---
    for nombre_db, attr_db in list(actuales.items()):
        if nombre_db not in nombres_en_plantilla:
            try:
                db.begin_nested() 
                db.delete(attr_db)
                db.flush()
                print(f"{indent}   🗑️ Atributo eliminado: {nombre_db}")
            except IntegrityError:
                db.rollback()


def sincronizar_recursivo(db: Session, nodo: dict, mapa_categorias: dict, mapa_atributos: dict, parent_id: int = None, tipo_raiz: str = None, ruta_nombres: list = None, level: int = 0):
    if ruta_nombres is None: ruta_nombres = []
    
    indent = "  " * level
    nombre = nodo["nombre"]
    if nombre.lower() == "todos": return

    # --- DETECCIÓN DE TIPO DE RAÍZ FUNCIONAL ---
    # Si el nombre es "Ropa", "Calzado", etc., actualizamos el tipo_raiz para todos sus descendientes
    nuevo_tipo_raiz = tipo_raiz
    if nombre.lower() in ["ropa", "calzado", "bolsos", "accesorios"]:
        nuevo_tipo_raiz = nombre.lower()

    ruta_actual = ruta_nombres + [nombre.lower()]
    genero_valor = nodo.get("genero") or None

    clave_cache = (nombre, parent_id)
    categoria = mapa_categorias.get(clave_cache)

    if categoria:
        print(f"{indent}🆗 Categoría existente: {nombre}")
    else:
        categoria = Categoria(nombre=nombre, descripcion=nodo.get("descripcion", ""), genero=genero_valor, parent_id=parent_id, activo=True)
        db.add(categoria)
        db.flush() 
        mapa_categorias[clave_cache] = categoria
        print(f"{indent}✨ Nueva categoría: {nombre}")

    # Ahora tipo_raiz tendrá el valor "ropa", "calzado", etc. cuando estemos dentro de esas ramas
    sincronizar_atributos(db, categoria.id, nombre, nuevo_tipo_raiz, ruta_actual, mapa_atributos, indent)

    for hijo in nodo.get("hijos", []):
        sincronizar_recursivo(db, hijo, mapa_categorias, mapa_atributos, parent_id=categoria.id, tipo_raiz=nuevo_tipo_raiz, ruta_nombres=ruta_actual, level=level+1)

# ==============================================================================
# 3. BLOQUE DE EJECUCIÓN
# ==============================================================================
def poblar_categorias():
    print("\n" + "="*50)
    print("🛠️  VERIFICANDO TABLAS EN LA BASE DE DATOS...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas listas.")
    print("="*50 + "\n")

    db = SessionLocal()
    try:
        print("🚀 INICIANDO SINCRONIZACIÓN DE CATEGORÍAS...\n")
        
        todas_categorias = db.query(Categoria).all()
        mapa_categorias = {(c.nombre, c.parent_id): c for c in todas_categorias}

        todos_atributos = db.query(AtributoCategoria).all()
        mapa_atributos = {}
        for a in todos_atributos:
            if a.categoria_id not in mapa_atributos: mapa_atributos[a.categoria_id] = {}
            mapa_atributos[a.categoria_id][a.nombre] = a
        
        for cat in categorias_master:
            sincronizar_recursivo(db, cat, mapa_categorias, mapa_atributos)
            
        db.commit()
        print("\n" + "="*50)
        print("🎉 PROCESO FINALIZADO CON ÉXITO")
        print("="*50 + "\n")
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR CRÍTICO: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    poblar_categorias()