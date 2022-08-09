from abc import ABC, abstractmethod
from itertools import chain
import re
from datetime import datetime
from ..controllers.controllers_querys import HauszMapa, CallProcedureHauszMapa
from ..brands.brand_viscardi import Viscardi
from ..brands.brand_gaudi import Gaudi
from ..brands.brand_itagres import Itagres
from ..brands.brand_elizabeth import Elizabeth
from ..brands.brand_lexxa import Lexxa
from ..brands.brand_level import Level
from ..brands.brand_sense import Sense
from ..brands.brand_quikstep import QuickStep
from ..brands.update_balances import AtualizaSaldos


#Faz chamada das marcas que ira executar a procedure

class Marcas(ABC):
    @abstractmethod
    def get_saldos(self) -> None: pass


class BrandGaudi(Marcas):
    def get_saldos(self, valor) -> None:
        try:
            brand = 'Gaudi'
            gaudi = Gaudi(valor)
            gaudi.converter_imgpdf()
            dicts = gaudi.create_dataframe()
            gaudi.delete_upload_files()
            gaudi.delete_image_files()
            gaudi.dict_writer()

            return dicts, brand
        except:
            print('erro classe Gaudi')


class BrandElizabeth(Marcas):
    def get_saldos(self, valor) -> None:
        try:
            elizabeth = Elizabeth(valor)
            brand = 'Elizabeth'
            elizabeth.converter_imgpdf()
            dicts = elizabeth.reader_imagem()
            #elizabeth.dict_writer()
            elizabeth.delete_upload_files()
            elizabeth.delete_image_files()
            elizabeth.dict_writer()
            return dicts, brand
        except:
            print('Erro classe Elizabeth')


class BrandItagres(Marcas):
    def get_saldos(self, valor) -> None:
        try:
            itagres = Itagres(valor)
            brand = 'Itagres'
            itagres.converter_imgpdf()
            dicts = itagres.imagem_reader()
            itagres.delete_upload_files()
            itagres.delete_image_files()
            itagres.dict_writer()

            return dicts, brand
        except:
            print("erro classe Itagres")


class BrandViscardi(Marcas):
    def get_saldos(self, valor):
        try:
            viscardi = Viscardi(valor)
            brand = 'Viscardi'
            viscardi.converter_imgpdf()
            dicts = viscardi.reader_imagem()
            viscardi.delete_upload_files()
            viscardi.delete_image_files()
            viscardi.dict_writer()

            return dicts, brand
        except:
            print("erro classe Viscardi")

class BrandLexxa(Marcas):
    def get_saldos(self, valor):
        lexxa = Lexxa(valor)
        brand ='Lexxa'
        lexxa.converter_imgpdf()
        dicts = lexxa.create_dataframe()
        lexxa.delete_upload_files()
        lexxa.delete_image_files()
        lexxa.dict_writer()
        return dicts, brand

class BrandLevel(Marcas):
    def get_saldos(self, valor) -> None:
        try:
            level = Level(valor)
            brand = 'Level'
            dicts = level.read_excel()
            level.delete_upload_files()
            level.delete_image_files()
            level.dict_writer()
            print(dicts)
            return dicts, brand
        except:
            print("erro classe Level")

class BrandSense(Marcas):
    def get_saldos(self, valor):
        try:
            sense = Sense(valor)
            brand = 'Sense'
            sense.converter_imgpdf()
            dicts = sense.create_dataframe()
            sense.delete_upload_files()
            sense.delete_image_files()
            sense.dict_writer()
            return dicts, brand
        except:
            print("erro classe Sense")

class BrandQuickstep(Marcas):
    def get_saldos(self, valor) -> None:
        try:
            quickstep = QuickStep(valor)
            brand = 'Quickstep'
            quickstep.converter_imgpdf()
            dicts = quickstep.reader_imagem()
            quickstep.delete_upload_files()
            quickstep.delete_image_files()
            quickstep.dict_writer()
            return dicts, brand
        except:
            print("erro classe Quickstep")


class BrandSaldoCrossDocking:
    def get_saldos(self, valor) -> None:
        try:
            crossdocking = AtualizaSaldos(valor)
            brand = 'SaldoFornecedor'
            dicts = crossdocking.reader_excel_file()
            return dicts, brand
        except:
            print("erro Class Crossdocking")

        #crossdocking.delete_upload_files()
        #crossdocking.delete_image_files()


class MarcaFactory:
    @staticmethod
    def get_marca(brand: str):

        if re.search('gaudi.?', brand, re.IGNORECASE):
            return BrandGaudi()

        if re.search('elizabeth.?', brand, re.IGNORECASE):
            return BrandElizabeth()

        if re.search('itagres.?', brand, re.IGNORECASE):
            return BrandItagres()

        if re.search('viscardi.?', brand, re.IGNORECASE):
            return BrandViscardi()

        if re.search('lexxa.?', brand, re.IGNORECASE):
            return BrandLexxa()

        if re.search('level.?', brand, re.IGNORECASE):
            return BrandLevel()

        if re.search('sense.?', brand, re.IGNORECASE):
            return BrandSense()

        if re.search('quick.?', brand, re.IGNORECASE):
            return BrandQuickstep()

        if re.search(r'[A-Z-a-z].*\.xlsx.?', brand, re.IGNORECASE):
            return BrandSaldoCrossDocking()


class Produto:
    def __init__(self, path):
        self.path = path

    def retorna_marca(self):
        lista_dicts = []
        valor = self.path
        marcas = MarcaFactory.get_marca(valor)
      
        dicts, brands = marcas.get_saldos(valor)
        if next(filter(lambda x: x['MARCA'] == brands, dicts), None):
            for items in dicts:
               
                exec_call = HauszMapa(items['SKU'], items['IDMARCA'],items['SALDO'])
                
                dicts = exec_call.select_hausz_mapa_produtos()
               
                listas = list(chain(dicts))
             
         
                for items in listas:
                    print('SKU',items)
                    if isinstance(items,dict):
                       
                        call_fornecedor_estoque = CallProcedureHauszMapa(items['SKU'],items['SALDO'], items['IDMARCA'], items['Marca'],items['NomeProduto'])
                   
                        dicts_values = call_fornecedor_estoque.call_procedure_atualiza_estoque_fornecedor()

                        lista_dicts.append(dicts_values)

        return  lista_dicts