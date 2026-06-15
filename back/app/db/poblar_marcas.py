from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base

from app.models.producto_model import Producto
from app.models.variantes_model import Variante
from app.models.variante_imagen_model import Imagen
from app.models.marcas_model import Marca
from app.models.categorias_model import Categoria
from app.models.proveedores_model import Proveedor


# Lista de marcas de ropa (puedes agregar todas las que quieras)
marcas_lista = [
    # —————————————— DEPORTIVAS GLOBALES ——————————————
    "Nike", "Adidas", "Puma", "Reebok", "Under Armour", "Vans", "Converse", "New Balance", "Fila", "ASICS",
    "Skechers", "Saucony", "Mizuno", "Brooks", "Hoka One One", "Salomon", "Columbia", "The North Face",
    "Patagonia", "Oakley", "Quiksilver", "Billabong", "Rip Curl", "DC Shoes", "Element", "Volcom", "Kappa",
    "Lotto", "Diadora", "Umbro", "Mammut", "Merrell", "Teva",

    # —————————————— MODA EUROPEA ——————————————
    "Zara", "H&M", "Bershka", "Pull & Bear", "Massimo Dutti", "Stradivarius",
    "Mango", "COS", "Armani", "Versace", "Dolce & Gabbana", "Valentino", "Roberto Cavalli",
    "Moschino", "Bally", "Benetton", "Max Mara", "Etro", "Marni", "Iceberg", "Trussardi",
    "Brunello Cucinelli", "Ermenegildo Zegna", "Moncler", "Paul Smith", "Ted Baker", "Vivienne Westwood",

    # —————————————— MODA FRANCESA ——————————————
    "Chanel", "Louis Vuitton", "Dior", "Hermès", "Givenchy", "Balenciaga", "Saint Laurent", "Celine",
    "Lanvin", "Jean Paul Gaultier", "Longchamp", "Lacoste", "Petit Bateau", "A.P.C.", "Sandro", "Maje",
    "Balmain", "Kenzo", "Isabel Marant", "Roger Vivier", "Agnes b.", "Carven", "Sézane", "Courrèges",
    "Christian Louboutin",

    # —————————————— MODA ITALIANA ——————————————
    "Gucci", "Prada", "Versace", "Armani Exchange", "Armani Jeans", "Bottega Veneta",
    "Fendi", "Moschino", "Max Mara", "Etro", "Trussardi", "Valentino", "Tod's", "Missoni", "Brunello Cucinelli",
    "DSquared2", "Roberto Cavalli", "Miu Miu", "Moncler", "Marni", "Salvatore Ferragamo",

    # —————————————— MODA ESPAÑOLA ——————————————
    "Desigual", "Replay", "Cortefiel", "Springfield", "Adolfo Dominguez", "Hoss Intropia",
    "Bimba Y Lola", "Sita Murt", "Bershka", "Zara Home", "Uterqüe", "Scalpers", "Paco Rabanne",
    "Munich", "Pikolinos", "Castañer", "Loewe", "Tous", "MIM",

    # —————————————— MODA AMERICANA ——————————————
    "Ralph Lauren", "Tommy Hilfiger", "Calvin Klein", "Coach", "Michael Kors",
    "Kate Spade", "Tory Burch", "Marc Jacobs", "Guess", "Hollister", "Abercrombie & Fitch",
    "Levi's", "DKNY", "Gap", "Old Navy", "Banana Republic", "Abercrombie", "American Eagle",
    "True Religion", "Lucky Brand", "Aeropostale", "Tumi", "Tom Ford", "J.Crew",

    # —————————————— MODA ASIÁTICA ——————————————
    "Uniqlo", "Muji", "GU", "IZOD", "Evisu", "A Bathing Ape", "Comme des Garçons", "Yohji Yamamoto",
    "Issey Miyake", "Undercover", "Supreme Japan", "NEIGHBORHOOD", "Wacko Maria",
    "Onitsuka Tiger", "Ree Bok (JP)", "Descente", "Snow Peak", "Visvim", "Tadashi Shoji",

    # —————————————— STREETWEAR / SKATE ——————————————
    "Supreme", "Stüssy", "Palace", "Anti Social Social Club", "Off-White", "Billionaire Boys Club",
    "Diamond Supply Co.", "Thrasher", "The Hundreds", "Obey", "HUF", "Independent", "DC Shoes", "Vans",

    # —————————————— LUJO / HIGH FASHION ——————————————
    "Hermès", "Chloé", "Balenciaga", "Givenchy", "Celine", "Saint Laurent", "Alexander McQueen",
    "Balmain", "Maison Margiela", "Rick Owens", "Berluti", "Acne Studios", "Dries Van Noten",
    "Ann Demeulemeester", "Alaïa", "Delpozo", "Jean-Charles de Castelbajac",

    # —————————————— CALZADO ——————————————
    "Timberland", "Clarks", "Dr. Martens", "Birkenstock", "UGG", "Toms", "Sperry", "Keen",
    "Geox", "Camper", "Ecco", "Teva", "K-Swiss", "Rockport",

    # —————————————— ACCESORIOS / RELOJES ——————————————
    "Rolex", "Omega", "Tag Heuer", "Tissot", "Seiko", "Casio", "Fossil", "Swatch",
    "Ray-Ban", "Oakley", "Persol", "Armani Exchange", "Bulova", "Citizen",

    # —————————————— TECNOLOGÍA (MUNDIAL) ——————————————
    "Apple", "Samsung", "Google", "Microsoft", "Intel", "AMD", "NVIDIA", "IBM",
    "Sony", "LG", "Panasonic", "Toshiba", "Sharp", "Philips", "Haier", "Lenovo",
    "HP", "Dell", "Asus", "Acer", "MSI", "Razer", "Alienware", "Google Pixel", "OnePlus",
    "Xiaomi", "Oppo", "Vivo", "Realme", "Huawei", "ZTE", "Motorola", "BlackBerry",

    # —————————————— TECNO WEARABLE / AUDIO ——————————————
    "Bose", "Beats", "Sennheiser", "JBL", "Harman Kardon", "Bang & Olufsen",
    "Sony WH-1000XM", "Jabra", "Marshall", "AKG", "Audio-Technica", "Plantronics",

    # —————————————— AUTOMOCIÓN TECNO ——————————————
    "Tesla", "Ford", "Chevrolet", "Toyota", "Honda", "BMW", "Mercedes-Benz",
    "Audi", "Volkswagen", "Porsche", "Ferrari", "Lamborghini", "Maserati",

    # —————————————— TECNO JUEGOS ——————————————
    "Nintendo", "PlayStation", "Xbox", "Atari", "Sega", "Valve", "Epic Games",
    "Ubisoft", "EA Games", "Activision", "Blizzard",

    # —————————————— TECNO SOFTWARE / WEB ——————————————
    "Facebook", "Instagram", "Twitter", "Snapchat", "TikTok", "LinkedIn", "Pinterest",
    "Reddit", "YouTube", "WhatsApp", "Telegram", "WeChat", "Discord",

    # —————————————— MODA INFANTIL ——————————————
    "Carter's", "OshKosh B'gosh", "Gymboree", "The Children's Place",
    "Petit Bateau", "Hanna Andersson", "Baby Gap", "Seed Heritage",

    # —————————————— MODA DEPORTIVA ESPECIALIZADA ——————————————
    "Lululemon", "Athleta", "Gymshark", "Fabletics", "Under Armour Women",
    "Fila Sport", "Nike SB", "Adidas Originals", "Puma Sportstyle",

    # —————————————— MARCAS DE JEANS ——————————————
    "Diesel", "True Religion", "7 For All Mankind", "AG Jeans", "Kings of Indigo",
    "Pepe Jeans", "G-Star RAW", "Replay", "Lee", "Wrangler",

]

def poblar_marcas():
    db: Session = SessionLocal()

    # Eliminamos duplicados de la lista
    marcas_unicas = list(set(marcas_lista))

    for nombre in marcas_unicas:
        # Verifica si la marca ya existe en la base de datos
        if not db.query(Marca).filter(Marca.nombre == nombre).first():
            marca = Marca(nombre=nombre)
            db.add(marca)

    db.commit()  # Un solo commit al final
    db.close()
    print("✅ Marcas insertadas correctamente (ignorando duplicados).")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    poblar_marcas()