from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime

db = SQLAlchemy()
def configure(app):
    db.init_app(app)
    app.db = db

class Brands:
    def __init__(self):
        self.list_dicts = []
        self.data = str(datetime.today().strftime('%Y-%m-%d %H:%M'))

    def select_marcas(self):
        lista_dict_marcas =[]

        with db.engine.connect() as conn:

            exec = (text("""
                      SELECT  DISTINCT TOP 10 pmarca.Marca,COUNT(pbasico.SKU) as 'TOTALSKUS',
                        CASE
                            WHEN pmarca.BitAtivo = 1 THEN 'MarcaAtiva'
                            WHEN pmarca.BitAtivo = 0 THEN 'MarcaInativa'
                            ELSE 'NaoAvaliado'
                        END 'StatusMarcaAtiva'
                        FROM [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
                        JOIN [HauszMapa].[Produtos].[Marca] as pmarca
                        ON pmarca.IdMarca = pbasico.IdMarca
                        JOIN [HauszMapa].[Produtos].[ProdutosSaldos] as psaldo
                        ON psaldo.SKU = pbasico.SKU
                        GROUP BY pmarca.IdMarca,pmarca.Marca, pmarca.BitAtivo
                        """))
                      
            exec_produtos = conn.execute(exec).all()

            for marcas in exec_produtos:
                lista_dict_marcas.append(marcas)
        return lista_dict_marcas


    
    def vendas_mes_marcas_hausz_mapa(self, mes):
        lista_dict_marcas =[]

        with db.engine.connect() as conn:

            exec = (text("""
                SELECT DISTINCT pmarca.Marca
                ,convert(char(06),(getdate()),101) AS 'mesatual'
                ,SUM(pflexy.[ValorTotal]) OVER(PARTITION BY pmarca.Marca) AS Total
                FROM [HauszMapa].[Pedidos].[ItensFlexy] as iflexy
                JOIN [HauszMapa].[Pedidos].[PedidoFlexy]  AS pflexy
                ON pflexy.CodigoPedido = iflexy.CodigoPedido
                JOIN [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
                ON pbasico.SKU = iflexy.SKU
                JOIN [HauszMapa].[Produtos].[Marca] as pmarca
                ON pmarca.IdMarca = pbasico.IdMarca
                WHERE pflexy.StatusPedido IN ('Pago','Entregue','NF Emitida','Saiu Para Entrega'
                ,'Em trânsito HUB Sumaré') and convert(char(06),(getdate()),101) = '{}'""".format(mes)))
            exec_produtos = conn.execute(exec).all()

            for marcas in exec_produtos:
                items = {
                    'Marca':marcas['Marca'],
                    'Total':marcas['Total'],
                    'Data':marcas['mesatual']
                }
                lista_dict_marcas.append(items)
        return lista_dict_marcas


    def consultas_ranking_estoque_hausz(self):
        lista_produtos = []
        with db.engine.connect() as conn:
           
            exec = (text("""
                SELECT DISTINCT pmarca.Marca
                ,SUM(pbasico.[SaldoAtual]) OVER(PARTITION BY pmarca.Marca) AS Total
                FROM [HauszMapa].[Produtos].[ProdutoBasico]  as pbasico
                JOIN [HauszMapa].[Produtos].[Marca] as pmarca
                ON pmarca.IdMarca = pbasico.IdMarca
                JOIN [HauszMapa].[Estoque].[Estoque] as pestoque
                ON pestoque.IdEstoque = pbasico.EstoqueAtual
                WHERE NomeEstoque in ('Fisico','Matriz','FisicoSWSC')"""))
            exec_produtos = conn.execute(exec).all()
            for marcas in exec_produtos:
                items = {
                    'Marca':marcas['Marca'],
                    'Total':round(float(marcas['Total']),2)
                }
                print(items)
                lista_produtos.append(items)
        return lista_produtos
        


                            
