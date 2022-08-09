from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


def configure(app):
    db.init_app(app)
    app.db = db


#informações exibidas no DashAdmin

class DashAdmin:
    def __init__(self, bit):
        self.data = str(datetime.today().strftime('%Y-%m-%d %H:%M'))
        self.bit = bit

    def resumo_produtos(self, bit):
        lista_dicts = []
        query_atualizados = db.engine.execute("""
            SELECT DISTINCT  TOP(5) pmarca.Marca,pbasico.[IdProduto],pbasico.[SKU]
            ,pbasico.[NomeProduto],pbasico.[SaldoAtual],pestoque.NomeEstoque, psaldo.Quantidade
            ,format(psaldo.DataAtualizado, 'd', 'pt-BR') as 'dataatualizado',psaldo.DataAtualizado,
            CASE 
                WHEN format(psaldo.DataAtualizado, 'd', 'pt-BR') = format(getdate(), 'd', 'pt-BR') THEN 'Atualizado'
                WHEN format(psaldo.DataAtualizado, 'd', 'pt-BR') <> format(getdate(), 'd', 'pt-BR') THEN 'NaoAtualizado'
            ELSE 'Verificar'
            END 'StatusMarcas'
            FROM [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
            JOIN [HauszMapa].[Produtos].[Marca] AS pmarca
            on pmarca.IdMarca = pbasico.IdMarca
            JOIN [HauszMapa].[Estoque].[Estoque] AS pestoque
            on pestoque.[IdEstoque] = pbasico.EstoqueAtual
            JOIN [HauszMapa].[Produtos].[ProdutosSaldos] AS psaldo
            on psaldo.SKU = pbasico.SKU
            WHERE pestoque.bitCrossDocking  like '%{}%' and psaldo.Quantidade > 0
            order by psaldo.DataAtualizado desc""".format(bit))
        for query_dict in query_atualizados:
            dict_itens = {

                'IdProduto': query_dict[1],
                'Marca': query_dict[0],
                'SKU': query_dict[2],
                'NomeProduto': query_dict[3],
                'Quantidade': float(query_dict[4]),
                'Verificar': query_dict[9],
                'Data': query_dict[7]}

            lista_dicts.append(dict_itens)
        cont = len(lista_dicts)

        return lista_dicts

    @staticmethod
    def cont_produtos(bit):
        lista_dicts = []
        query_atualizados = db.engine.execute("""
            SELECT pbasico.NomeProduto,pbasico.SaldoAtual,psaldos.[SKU]
            ,psaldos.[IdMarca],psaldos.[Quantidade],Cast(psaldos.[DataAtualizado] as date) AS dataatual
            FROM [HauszMapa].[Produtos].[ProdutosSaldos] as psaldos
            join [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
            on pbasico.SKU = psaldos.SKU
            JOIN [HauszMapa].[Estoque].[Estoque] AS pestoque
            on pestoque.[IdEstoque] = pbasico.EstoqueAtual
            WHERE pestoque.bitCrossDocking = {}
            """.format(bit))
        for dicts in query_atualizados:
            dict_itens = {
                'id': dicts[0]}
            lista_dicts.append(dict_itens)
        cont = len(lista_dicts)
        return cont

    @staticmethod
    def produto_estoque():
        lista_dicts = []
        estoque_disp = db.engine.execute("""SELECT pbasico.NomeProduto,pbasico.SaldoAtual,psaldos.[SKU]
            ,psaldos.[IdMarca],psaldos.[Quantidade],Cast(psaldos.[DataAtualizado] as date) AS dataatual
            FROM [HauszMapa].[Produtos].[ProdutosSaldos] as psaldos
            join [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
            on pbasico.SKU = psaldos.SKU
            JOIN [HauszMapa].[Estoque].[Estoque] AS pestoque
            on pestoque.[IdEstoque] = pbasico.EstoqueAtual
            and pestoque.bitCrossDocking = 0 and psaldos.[Quantidade] >0""")
        for estoques in estoque_disp:
            dict_itens = {
                'IdMarca': estoques[3]}
            lista_dicts.append(dict_itens)

        cont = len(lista_dicts)
        return cont





