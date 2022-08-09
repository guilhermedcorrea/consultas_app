import re
from itertools import chain
from datetime import datetime
from sqlalchemy import text
import itertools
from flask_sqlalchemy import SQLAlchemy
import os
db = SQLAlchemy()


def configure(app):
    db.init_app(app)
    app.db = db


# faz a consulta na tabela [HauszMapa].[Produtos].[ProdutoBasico] as basico / Produtos.Marca as brand
class HauszMapa:
    def __init__(self, sku, idmarca, saldos):
        self.idmarca = idmarca
        self.saldos = saldos
        self.sku = sku

    def select_hausz_mapa_produtos(self):
        lista_dicts = []
        with db.engine.connect() as conn:
            exec = (text("""SELECT basico.[SKU] ,basico.[IdMarca], brand.Marca, basico.NomeProduto
                        FROM [HauszMapa].[Produtos].[ProdutoBasico] as basico
                        join Produtos.Marca as brand
                        on brand.IdMarca = basico.IdMarca
                        WHERE basico.[SKU] in ('{}')""".format(self.sku)))
            exec_produtos = conn.execute(exec).all()

            if next(filter(lambda x: x[0] == self.sku, exec_produtos), None):
                print('exec hauz mapa', exec_produtos)

                for items in exec_produtos:
                    dict_items = {
                        'SKU': items[0],
                        'IDMARCA': items[1],
                        'Marca': items[2],
                        'NomeProduto': items[3],
                        'SALDO': self.saldos}
                    lista_dicts.append(dict_items)
                    # return dict_items
                
        return lista_dicts

    @property
    def saldos(self):
        return self._saldos

    @saldos.setter
    def saldos(self, valor):
        if isinstance(valor, float):
            self._saldos = valor
            return valor

        else:
            self._saldos = float(0)

    @property
    def sku(self):
        return self._sku

    @sku.setter
    def sku(self, valor):
        if isinstance(valor, str):
            self._sku = valor
            return valor
        else:
            self._sku = 'naoencontrado'


class CallProcedureHauszMapa:
    def __init__(self, sku, saldo, idmarca, nome, marca):
        self.sku = sku
        self.saldo = saldo
        self.idmarca = idmarca
        self.data = str(datetime.today().strftime('%Y-%m-%d %H:%M'))
        self.nome = nome
        self.marca = marca

    #Procedure AtualizaSaldos
    # call Prcedure/ Executa a procedure Estoque.SP_AtualizaEstoqueFornecedor passando quantidade, codigo e idmarca
    def call_procedure_atualiza_estoque_fornecedor(self):

        dict_items = {
            'sku': self.sku,
            'saldo': self.saldo,
            'IdMarca': self.idmarca,
            'NomeProduto': self.nome,
            'Marca': self.marca,
            'data': self.data
        }
        print('produtoooo', self.saldo, self.sku, self.idmarca)
        try:
            with db.engine.begin() as conn:
                exec = (text(
                    """EXEC Estoque.SP_AtualizaEstoqueFornecedor @Quantidade = {}, @CodigoProduto = '{}', @IdMarca = {}""".format(
                        self.saldo, self.sku, self.idmarca)))
                exec_produtos = conn.execute(exec)

            return dict_items
        except:
            print('erro')


class ResumoDash:
    def __init__(self):
        self.data = str(datetime.today().strftime('%Y-%m-%d %H:%M'))

    def marcas_atualizadas_dia_atual(self):
        lista_dicts = []
        with db.engine.connect() as conn:
            exec = (text("""SELECT distinct marcas.[IdMarca],marcas.[Marca],
                                count(marcas.[Marca]) as 'total'
                                FROM [HauszMapa].[Produtos].[Marca] as marcas     
                                where marcas.[IdMarca] in 
                                (SELECT IdMarca From [HauszMapa].[Produtos].[ProdutosSaldos]
                                Where convert(VARCHAR, [DataAtualizado], 23) =  convert(VARCHAR, getdate(), 23))
                                group by marcas.[IdMarca],marcas.[Marca]"""))
            exec_resumo_dash = conn.execute(exec).all()

            for exec in exec_resumo_dash:
                items = {
                    'IdMarca': exec[0],
                    'Marca': exec[1],
                    'Total': exec[2]}
                lista_dicts.append(items)

        total_marcas = len(lista_dicts)
        return total_marcas, lista_dicts

    def marcas_full(self):

        with db.engine.connect() as conn:
            exec = (text("""SELECT count([IdMarca]) as 'marcas'
                                FROM [HauszMapa].[Produtos].[Marca]"""))
            exec_resumo_dash = conn.execute(exec).first()

            return exec_resumo_dash

    @staticmethod
    def resumo_marcas(page=1):

        lista_dicts = []

        with db.engine.connect() as conn:
            exec = (text("""
                                DECLARE @PageNumber AS INT
                                DECLARE @RowsOfPage AS INT
                                SET @PageNumber= {}
                                SET @RowsOfPage= 10
                                SELECT pmarca.Marca,pmarca.PrazoFabricacao
                                        ,pmarca.PedidoMinimo,pbasico.[SKU]
                                        ,pbasico.[NomeProduto],pestoq.NomeEstoque
                                        ,pestoq.PrazoAdicional,pestoq.PrioridadeEstoque
                                        ,pbasico.[SaldoAtual],
                                        CASE
                                                WHEN pmarca.BitAtivo = 1 THEN 'Produto Ativo'
                                                WHEN pmarca.BitAtivo = 0 THEN 'Produto Inativo'
                                        ELSE 'Nao foi possivel verificar'
                                        END 'Statusmarca'
                                        FROM [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
                                        join [HauszMapa].[Produtos].[Marca] as pmarca
                                        on pbasico.IdMarca = pmarca.IdMarca
                                        join [HauszMapa].[Estoque].[Estoque] as pestoq
                                        on pestoq.IdEstoque = pbasico.[EstoqueAtual]
                                        order by pbasico.[SaldoAtual]
                                        OFFSET (@PageNumber-1)*@RowsOfPage ROWS
                                        FETCH NEXT @RowsOfPage ROWS ONLY """.format(page)))
            exec_resumo_dash = conn.execute(exec).all()

            for exec in exec_resumo_dash:
                dict_itens = {'Marca': exec[0],
                              'PrazoFabricacao': exec[1],
                              'PedidoMinimo': exec[2],
                              'SKU': exec[3],
                              'NomeProduto': exec[4],
                              'NomeEstoque': exec[5],
                              'PrazoAdicional': exec[6],
                              'PrioridadeEstoque': exec[7],
                              'SaldoAtual': exec[8],
                              'Statusmarca': exec[9]
                              }

                lista_dicts.append(dict_itens)

        return lista_dicts

    def produtos_saldo(self):
        lista_dicts = []
        with db.engine.connect() as conn:
            exec = (text("""
                                SELECT distinct	
                                pbasico.[SaldoAtual],pbasico.SKU
                                FROM [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
                                where pbasico.SaldoAtual > 0 and pbasico.BitAtivo = 1"""))
            exec_resumo_dash = conn.execute(exec).all()

            for exc in exec_resumo_dash:
                dicts = {
                    'SKU': exc[0],
                    'SaldoAtual': exc[1]}

                lista_dicts.append(dicts)

        cont = int(len(lista_dicts))
        return cont

    def marcas_desativadas(self):

        lista_dicts = []
        with db.engine.connect() as conn:
            exec = (text(""" SELECT [IdMarca],Marca
                                        FROM [HauszMapa].[Produtos].[Marca]
                                        where BitAtivo = 0 """))
            exec_resumo_dash = conn.execute(exec)
            for exc in exec_resumo_dash:
                dicts = {
                    'IdMarca': exc[0],
                    'Marca': exc[1]
                }

                lista_dicts.append(dicts)

        cont = int(len(lista_dicts))
        return cont

    def saldo_fisico(self):
        lista_dicts = []

        with db.engine.connect() as conn:
            exec = (text("""
                                SELECT distinct pbasico.SKU,pbasico.[NomeProduto]
                                ,pbasico.[SaldoAtual],pbasico.EstoqueAtual
                                FROM [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
                                where pbasico.EstoqueAtual in (2,1) and pbasico.SaldoAtual > 0"""))
            exec_resumo_dash = conn.execute(exec).all()
            for exc in exec_resumo_dash:
                dicts = {
                    'SKU': exc[0],
                    'NomeProduto': exc[1],
                    'SaldoAtual': exc[2],
                    'EstoqueAtual': exc[3]}
                lista_dicts.append(dicts)

        cont = len(lista_dicts)
        total = self.produtos_saldo()
        total_valor = round(cont / int(total) * 100, 2)
        return total_valor

    @staticmethod
    def porcentagem_marcas(atualizados, total):
        return round(atualizados / int(total) * 100, 2)

    @staticmethod
    def nao_atualizado(atualizado, totmarca):
        cont = int(atualizado) - int(totmarca)
        return cont


def total_marcas_atualizadas():
    lista_dicts = []

    exec_resumo_dash = db.engine.execute("""SELECT distinct marcas.[IdMarca],marcas.[Marca],
                        count(marcas.[Marca]) as 'total'
                        FROM [HauszMapa].[Produtos].[Marca] as marcas     
                        (SELECT IdMarca From [HauszMapa].[Produtos].[ProdutosSaldos]
                        Where convert(VARCHAR, [DataAtualizado], 23) =  convert(VARCHAR, getdate(), 23) )
                        group by marcas.[IdMarca],marcas.[Marca]""").all()

    for exec in exec_resumo_dash:
        items = {
            'IdMarca': exec[0],
            'Marca': exec[1],
            'Total': exec[2]}

        lista_dicts.append(items)

    total_marcas = len(lista_dicts)

    return total_marcas, lista_dicts


class GraficosDash:
    def __inif__(self):
        self.data = str(datetime.today().strftime('%Y-%m-%d %H:%M'))

    def grafico_vendas_dia_marca(self):
        lista_dicts = []

        exec_resumo_dash = db.engine.execute("""SELECT  distinct pmarca.Marca,pflex.CodigoPedido
                        ,pflex.[StatusPedido],pflex.[ValorTotal]
                        ,pflex.[DataInserido] as 'datainserido'
                        ,convert(VARCHAR(5), pflex.[DataInserido] , 110) 'pvdia' 
                        FROM [HauszMapa].[Pedidos].[PedidoFlexy] pflex
                        join [HauszMapa].[Pedidos].[ItensFlexy] as iflex
                        on iflex.CodigoPedido = pflex.CodigoPedido
                        join Produtos.ProdutoBasico as pbasico
                        on pbasico.SKU = iflex.SKU
                        join Produtos.Marca as pmarca
                        on pmarca.IdMarca = pbasico.IdMarca
                        where convert(VARCHAR(5), pflex.[DataInserido] , 110)  = convert(varchar(5),getdate(),110) and StatusPedido ='Pago'
                        """).all()
        # convert(varchar(5),getdate(),110)
        for exec in exec_resumo_dash:
            items = {
                'Marca': exec[0],
                'CodigoPedido': exec[1],
                'StatusPedido': exec[2],
                'ValorTotal': float(exec[3]),
                'datainserido': exec[4]}

            lista_dicts.append(items)

        return lista_dicts