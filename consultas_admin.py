from flask import (Blueprint, render_template
, request, redirect, url_for, abort, current_app, send_from_directory,send_file, request)
from os.path import dirname, join
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_login import current_user
import os
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin import Admin
from sqlalchemy import text
from werkzeug.utils import secure_filename
import os
import flask_excel as excel
from flask_admin.menu import MenuLink

from flask_admin.base import BaseView, expose
from ..controllers.controllers_querys import ResumoDash
from config import UPLOADFOLDER


files = os.path.join(UPLOADFOLDER, 'atualizacaonewupdateapp','app','admin','files','adminuploads')
adm = Blueprint('adm', __name__)
excel.init_excel(current_app)

from ..models.hausz_mapa import (Usuarios, GrupoUsuario, ProdutosSaldos
, ProdutoPrazoProducFornec, DeparaProdutos, ColetadosDiario, ProdutoDetalhe)

from ..controllers.controllers_admin_files import DashAdmin
from ..controllers.factory_classes import Produto

db = SQLAlchemy()
def configure(app):
    db.init_app(app)
    app.db = db

class DefaultModelView(ModelView):
    page_size = 20

    create_modal = True
    # column_exclude_list = ['password_hash']
    column_display_pk = True
    column_searchable_list = ['SKU']
    can_view_details = True
    column_list = ['SKU', 'IdPrazos', 'PrazoEstoqueFabrica', 'PrazoProducao'
        , 'PrazoOperacional', 'PrazoFaturamento', 'PrazoTotal']

    # column_default_sort = ('last_name', False)
    column_filters = [

        'SKU', 'PrazoTotal', 'PrazoProducao'

    ]
    can_create = True
    can_edit = True
    Can_delete = True
    can_export = True

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login.login_usuario'))


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def Home(self):
        valore = 100
        produtos_crossdocking = DashAdmin(1).resumo_produtos(1)
        cont_natualizado = DashAdmin(1).cont_produtos(1)

        produtos_disponivel = DashAdmin(0).resumo_produtos(0)
        cont_estoque = DashAdmin(0).produto_estoque()
      
        dash = ResumoDash()
        total_marcas, dicts = dash.marcas_atualizadas_dia_atual()

        return self.render('admin/index.html', produtosc=produtos_crossdocking, cont_natualizado=cont_natualizado
                           , produtoe=produtos_disponivel, cont_estoque=cont_estoque, atualizado_dia_marca = total_marcas)
    # pass
    # def is_accessible(self):
    #   return current_user.is_authenticated


admin = Admin(current_app, name='HauszAdmin', template_mode='bootstrap3', index_view=MyAdminIndexView())
current_app.config['FLASK_ADMIN_FLUID_LAYOUT'] = True


class CommentView(ModelView):
    create_modal = True


class UploadfilesView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/uploads.html')

    @expose('/uploads')
    def upload_arquivos(self):
        files = os.listdir(os.path.join(UPLOADFOLDER,'atualizacaonewupdateapp','app','uploads'))
        return self.render('admin/uploads.html', files=files)

    @expose('/uploads', methods=['POST'])
    def upload_files(self):
        uploaded_file = request.files['file']

        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:

                return "Invalid image", 400
         
            uploaded_file.save(os.path.join(UPLOADFOLDER,'atualizacaonewupdateapp','app','uploads',filename))
            dicts = Produto(os.path.join(UPLOADFOLDER,'atualizacaonewupdateapp','app','uploads',filename))
            dicts_products = dicts.retorna_marca()

            #print('aqui salvo',os.path.join(current_app.config['UPLOAD_PATH'], filename))
            return self.render("admin/informacoesestoque.html", produtos=dicts_products)

        return '', 204

    @expose('/uploads/<filename>')
    def upload(self,filename):
        filesaldo = os.path.join(UPLOADFOLDER,'app','uploads',filename)

        dicts = Produto(filesaldo)

        dicts_products = dicts.retorna_marca()
        print(dicts_products)

        return send_from_directory(os.path.join(UPLOADFOLDER,'app','uploads',filename))
        #return render_template("admin/informacoesestoque.html", produtos=dicts_products)

    
    @expose("/modelosaldo", methods=['GET','POST'])
    def export_modelo_alteracao_saldo(self):
        return excel.make_response_from_array([['SKU','MARCA','SALDO']]
        ,"xlsx",file_name="exportmodelosaldo.xlsx")


    #Modelo arquivo alteração prazo fornecedor
    @expose("/modeloprazo", methods=['GET','POST'])
    def export_modelo_alteracao_prazo(self):
        return excel.make_response_from_array([['SKU','MARCA','PRAZO']]
        , "xlsx",  file_name="modeloalteracaodeprazo.xlsx")


admin.add_view(UploadfilesView(name='Uploadfiles', endpoint='uploads'))

class NotificationsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/notification.html')
  
    @expose('/saldofornecedoresumo/<int:page>', methods=('GET', 'POST'))
    def croosdocking_view(self, page):
      
        lista_dicts = []
        with db.engine.connect() as conn:
            exec = (text("""
                DECLARE @PageNumber AS INT
                DECLARE @RowsOfPage AS INT
                SET @PageNumber= {}
                SET @RowsOfPage= 10
                SELECT pestoque.NomeEstoque,pmarca.Marca
                ,pbasico.[SKU],pbasico.[NomeProduto]
                ,pbasico.[SaldoAtual],
                CASE
                    WHEN pbasico.BitAtivo = 1 THEN 'ProdutoAtivo'
                    WHEN pbasico.BitAtivo = 0 THEN 'ProdutoInativo'
                    ELSE 'NaoAvaliado'
                END 'STATUSPRODUTO',
                CASE
                    WHEN pbasico.[bitLinha] = 0 THEN  'ForaDeLinha'
                    WHEN pbasico.[bitLinha] = 1 THEN  'EmLinha'
                    ELSE 'NaoAvaliado'
                END 'STATUSPRODUTOLINHA',
                CASE
                    WHEN pestoque.NomeEstoque = 'Fisico' THEN 'Disponivel'
                    ELSE 'CrossDocking'
                END 'STATUSESTOQUE'
                FROM [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
                JOIN [HauszMapa].[Produtos].[Marca] as pmarca
                ON pmarca.IdMarca = pbasico.IdMarca
                JOIN [HauszMapa].[Estoque].[Estoque] as pestoque
                ON pestoque.IdEstoque = pbasico.EstoqueAtual
                where pestoque.NomeEstoque <> 'Fisico'
                ORDER BY pbasico.[SaldoAtual] DESC
                OFFSET (@PageNumber-1)*@RowsOfPage ROWS
                FETCH NEXT @RowsOfPage ROWS ONLY
                            
                            """.format(page)))
            saldos_crossdocking = conn.execute(exec).all()
            for saldos in saldos_crossdocking:
                dict_items = {
                    'Marca': saldos[1],
                    'SKU':saldos[2],
                    'NOMEPRODUTO':saldos[3],
                    'ESTOQUE':saldos[0],
                    'SALDOPRODUTO':saldos[4],
                    'STATUSPRODUTO':saldos[5],
                    'PRODUTOLINHA':saldos[6],
                    'STATUSESTOQUE':saldos[7]
                }

                lista_dicts.append(dict_items)
                

        return self.render('admin/saldofornecedor.html',page=page, produtos = lista_dicts)
      
   
    @expose('/saldodisponivel/<int:page>', methods=('GET', 'POST'))
    def disponivel_view(self, page):
        
        lista_dicts = []
        with db.engine.connect() as conn:

            exec = (text("""
               DECLARE @PageNumber AS INT
                DECLARE @RowsOfPage AS INT
                SET @PageNumber= {}
                SET @RowsOfPage= 10
                SELECT pestoque.NomeEstoque,pmarca.Marca
                ,pbasico.[SKU],pbasico.[NomeProduto]
                ,pbasico.[SaldoAtual],
                CASE
                    WHEN pbasico.BitAtivo = 1 THEN 'ProdutoAtivo'
                    WHEN pbasico.BitAtivo = 0 THEN 'ProdutoInativo'
                    ELSE 'NaoAvaliado'
                END 'STATUSPRODUTO',
                CASE
                    WHEN pbasico.[bitLinha] = 0 THEN  'ForaDeLinha'
                    WHEN pbasico.[bitLinha] = 1 THEN  'EmLinha'
                    ELSE 'NaoAvaliado'
                END 'STATUSPRODUTOLINHA',
                CASE
                    WHEN pestoque.NomeEstoque = 'Fisico' THEN 'Disponivel'
                    ELSE 'CrossDocking'
                END 'STATUSESTOQUE'
                FROM [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
                JOIN [HauszMapa].[Produtos].[Marca] as pmarca
                ON pmarca.IdMarca = pbasico.IdMarca
                JOIN [HauszMapa].[Estoque].[Estoque] as pestoque
                ON pestoque.IdEstoque = pbasico.EstoqueAtual
                where pestoque.NomeEstoque in ('Fisico')
                ORDER BY pbasico.[SaldoAtual] DESC
                OFFSET (@PageNumber-1)*@RowsOfPage ROWS
                FETCH NEXT @RowsOfPage ROWS ONLY
               """.format(page)))

            saldos_estoques = conn.execute(exec).all()
            for saldos in saldos_estoques:
                    dict_items = {
                    'Marca': saldos[1],
                    'SKU':saldos[2],
                    'NOMEPRODUTO':saldos[3],
                    'ESTOQUE':saldos[0],
                    'SALDOPRODUTO':saldos[4],
                    'STATUSPRODUTO':saldos[5],
                    'PRODUTOLINHA':saldos[6],
                    'STATUSESTOQUE':saldos[7] }

                    lista_dicts.append(dict_items)
          
           
        return self.render('admin/saldodisponivel.html', page=page, produtos = lista_dicts)

    @expose('/prazosprodutosmarcas/<int:page>', methods=('GET', 'POST'))
    def prazos_view(self, page=1):
        lista_dict_marcas =[]
        with db.engine.connect() as conn:
            exec = (text("""DECLARE @PageNumber AS INT
                      DECLARE @RowsOfPage AS INT
                      SET @PageNumber= {}
                      SET @RowsOfPage= 10
                      SELECT  distinct pmarca.Marca
                      ,cast(saldos.[DataAtualizado] as date) as 'ultimaatualizacao'
                      ,saldos.[IdMarca],
                      CASE
                          WHEN pmarca.BitAtivo = 1 THEN 'Marca Ativa'
                          WHEN pmarca.BitAtivo = 0 THEN 'Marca Inativa'
                      ELSE 'Nao Foi Possivel Verificar'
                      END 'StatusMarca'
                      FROM [HauszMapa].[Produtos].[ProdutosSaldos] as saldos
                      join [HauszMapa].[Produtos].[Marca] as pmarca
                      on pmarca.IdMarca = saldos.IdMarca
                      join Produtos.ProdutoBasico as pbasico
                      on pbasico.SKU = saldos.SKU
                      group by pmarca.Marca,cast(saldos.[DataAtualizado] as date)
                      ,saldos.[IdMarca],pmarca.BitAtivo
                      order by ultimaatualizacao desc 
                      OFFSET (@PageNumber-1)*@RowsOfPage ROWS
                      FETCH NEXT @RowsOfPage ROWS ONLY""".format(page)))
            exec_produtos = conn.execute(exec).all()

            for marcas in exec_produtos:
                lista_dict_marcas.append(marcas)

        return self.render('admin/prazosprodutos.html', page=page, produtos=lista_dict_marcas)
   
    @expose('/semcadastroprodutos', methods=('GET', 'POST'))
    def semcadastro_view(self):
        return self.render('admin/semcadastro.html')

    @expose('/produtosatualizados/<int:page>', methods=('GET','POST'))
    def produtos_atualizados(self, page=1):

        lista_dicts = []
        with db.engine.connect() as conn:
            exec = (text("""DECLARE @PageNumber AS INT
                      DECLARE @RowsOfPage AS INT
                      SET @PageNumber= {}
                      SET @RowsOfPage= 10
                      SELECT pmarca.Marca,pbasico.NomeProduto,psaldo.[IdProdutosSaldos]
                        ,psaldo.[SKU],psaldo.[IdMarca]  ,psaldo.[Quantidade]
                        ,pestoque.NomeEstoque
                        ,convert(VARCHAR, psaldo.[DataAtualizado] , 23),
                        CASE
                        WHEN pestoque.NomeEstoque = 'Fisico' THEN 'DISPONIVEL'
                        ELSE 'CrossDocking'
                        END 'STATUSESTOQUE',
                        CASE
                            WHEN convert(VARCHAR, [DataAtualizado], 23) =  convert(VARCHAR, getdate(), 23) THEN 'ProdutoAtualizado'
                            ELSE 'NAOATUALIZADO'
                        END 'STATUSATUALIZADO'
                        FROM [HauszMapa].[Produtos].[ProdutosSaldos] as psaldo
                        JOIN [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
                        ON pbasico.SKU = psaldo.SKU
                        JOIN [HauszMapa].[Produtos].[Marca] AS pmarca
                        ON pmarca.IdMarca = pbasico.IdMarca
                        JOIN [HauszMapa].[Estoque].[Estoque] as pestoque
                        ON pestoque.IdEstoque = pbasico.EstoqueAtual
                        ORDER BY psaldo.DataAtualizado DESC
                        OFFSET (@PageNumber-1)*@RowsOfPage ROWS
                        FETCH NEXT @RowsOfPage ROWS ONLY""".format(page)))
                                            
                                        
            exec_produtos = conn.execute(exec).all()
            for produto in exec_produtos:
                dict_items = {
                    'SKU':produto[3],
                    'MARCA':produto[0],
                    'NOMEPRODUTO':produto[1],
                    'SALDO':produto[5],
                    'ESTOQUE':produto[6],
                    'STATUSSTOQUE':produto[7],
                    'STATUSDATA':produto[8],
                    'DATAATUALIZACAO':produto[7]
                }

                lista_dicts.append(dict_items)

                                    
        return self.render('admin/produtoatualizado.html', page = page, produtos = lista_dicts)

  
    @expose('/statusmarcas/<int:page>', methods=('GET','POST'))
    def status_marca_produto(self, page=1):
        page = int(page)

        lista_produtos = []
        with db.engine.connect() as conn:
            exec = (text("""
            
               DECLARE @PageNumber AS INT
                DECLARE @RowsOfPage AS INT
                SET @PageNumber= {}
                SET @RowsOfPage= 10
                SELECT  pmarca.Marca,COUNT(pbasico.SKU) as 'TOTALSKUS',
                CASE
                WHEN pmarca.BitAtivo = 1 THEN 'MarcaAtiva'
                WHEN pmarca.BitAtivo = 0 THEN 'MarcaInativa'
                                    ELSE 'NaoAvaliado'
                END 'StatusMarcaAtiva'
                FROM [HauszMapa].[Produtos].[ProdutoBasico] as pbasico
                JOIN [HauszMapa].[Produtos].[Marca] as pmarca
                ON pmarca.IdMarca = pbasico.IdMarca
                
                GROUP BY pmarca.IdMarca,pmarca.Marca, pmarca.BitAtivo
                ORDER BY TOTALSKUS DESC
                OFFSET (@PageNumber-1)*@RowsOfPage ROWS
                FETCH NEXT @RowsOfPage ROWS ONLY
               
                """.format(page)))
   
            exec_produtos = conn.execute(exec).all()
            for produto in exec_produtos:
                lista_produtos.append(produto)

            self.render('admin/status_marca.html', produtos = lista_produtos, page=page)


                


class UserView(ModelView):
    can_set_page_size = True
    page_size = 15
    create_modal = True
    column_sortable_list = ('IdProduto', ('IdProduto', Usuarios.id_usuario))
    column_display_pk = True
    column_searchable_list = ['nome', 'email', 'datalogado', 'datacadastro', 'status_login', 'grupo']
    can_view_details = True
    column_list = ['id_usuario', 'id_grupo', 'nome', 'email', 'bitusuario', 'status_login', 'grupo']
    # column_default_sort = ('last_name', False)
    column_filters = ['nome', 'email', 'grupo', 'status_login', 'datalogado']
    column_sortable_list = ('id_usuario',)
    column_default_sort = 'id_usuario'


class Deparaview(ModelView):
    can_set_page_size = True
    page_size = 15
    create_modal = True
    column_sortable_list = ('IdProduto', ('IdProduto', DeparaProdutos.iddepara))
    column_display_pk = True
    column_searchable_list = ['marca', 'statusdepara', 'referenciahausz', 'nomeproduto']
    can_view_details = True
    column_list = ['iddepara', 'IdProduto', 'ean', 'statusdepara',
                   'referenciafabricante', 'referenciahausz', 'nomeproduto', 'idmarcahausz', 'marca', 'bitativo']
    # column_default_sort = ('last_name', False)
    column_filters = [

        'marca', 'statusdepara', 'referenciahausz', 'nomeproduto'

    ]
    can_create = True
    can_edit = True
    Can_delete = True
    can_export = True
    column_sortable_list = ('iddepara',)
    column_default_sort = 'iddepara'


'''
class ProdutoDetalheView(ModelView):
    can_set_page_size = True
    page_size = 15
    column_display_pk = True
    create_modal = True
    column_sortable_list = ('IdProduto', ('IdProduto', ProdutoDetalhe.IdProduto))
    column_searchable_list = ['SKU', 'IdMarca', 'DataAtualizado']
    can_view_details = True
    column_list = ['SKU', 'IdMarca', 'Descricao', 'QuantidadeMinima','TamanhoBarra','Garantia','FatorMultiplicador'
    ,'FatorUnitario','FatorVenda']
    # column_default_sort = ('last_name', False)
    column_filters = [
        'SKU', 'IdMarca'
    ]
    can_create = True
    can_edit = True
    Can_delete = True
    can_export = True
    column_display_all_relations = True
    column_sortable_list = ('IdProduto',)
    column_default_sort = 'IdProduto'
'''
class ProdutosSaldosView(ModelView):
    can_set_page_size = True
    page_size = 15
    column_display_pk = True
    create_modal = True
    column_sortable_list = ('IdProdutosSaldos', ('IdProdutosSaldos', ProdutosSaldos.IdProdutosSaldos))
    column_searchable_list = ['SKU', 'IdMarca', 'DataAtualizado']
    can_view_details = True
    column_list = ['SKU', 'IdMarca', 'Quantidade', 'DataAtualizado']
    # column_default_sort = ('last_name', False)
    column_filters = [

        'SKU', 'Quantidade', 'DataAtualizado'

    ]
    can_create = True
    can_edit = True
    Can_delete = True
    can_export = True
    column_display_all_relations = True
    column_sortable_list = ('IdProdutosSaldos',)
    column_default_sort = 'IdProdutosSaldos'



class ColetadosView(ModelView):
    create_modal = True
    column_display_pk = True
    column_searchable_list = ['referenciahausz', 'referenciafabricante', 'nomeproduto', 'saldo'
        , 'BitAtivo', 'dataalteracao']
    can_view_details = True
    column_list = ['referenciahausz', 'referenciafabricante', 'nomeproduto', 'CodBarras', 'saldo'
        , 'prazo', 'BitAtivo', 'alteradopor', 'dataalteracao']
    # column_default_sort = ('last_name', False)
    column_filters = [

        'referenciahausz', 'referenciafabricante', 'nomeproduto', 'BitAtivo',

    ]
    can_create = True
    can_edit = True
    Can_delete = True
    can_export = True


class IndesView(BaseView):
    @expose('/')
    def Home(self):
        valore = 100
        produtos_crossdocking = DashAdmin(1).resumo_produtos(1)
        cont_natualizado = DashAdmin(1).cont_produtos(1)

        produtos_disponivel = DashAdmin(0).resumo_produtos(0)
        cont_estoque = DashAdmin(0).produto_estoque()
        print(produtos_disponivel)

        return self.render('admin/index.html', produtosc=produtos_crossdocking, cont_natualizado=cont_natualizado
                          , produtoe=produtos_disponivel, cont_estoque=cont_estoque)

path = os.path.join(UPLOADFOLDER,'atualizacaonewupdateapp','app','admin','files','adminuploads')

admin.add_view(FileAdmin(path, '/adminuploads/', name='adminuploads'))
admin.add_view(NotificationsView(name='Notifications', endpoint='notify'))

admin.add_view(DefaultModelView(ProdutoPrazoProducFornec, db.session, category="Produtos"))
admin.add_view(ProdutosSaldosView(ProdutosSaldos, db.session, category="Produtos"))
admin.add_view(Deparaview(DeparaProdutos, db.session, category="Produtos"))
admin.add_view(ModelView(ColetadosDiario, db.session, category="Produtos"))

admin.add_sub_category(name="Links", parent_name="Produtos")

admin.add_view(UserView(Usuarios, db.session))

admin.add_link(MenuLink(name='Dashboard', url='/'))
admin.add_link(MenuLink(name='Sair', url='/logout'))
admin.add_link(MenuLink(name='Login', url='/login'))

@adm.route('/adminuploads/<name>')
def download_files_admin(name):

    path = os.path.join(UPLOADFOLDER,'atualizacaonewupdateapp'
    ,'app','admin','files','adminuploads')
    filename=os.path.join(path, name)

    return send_from_directory(path,name)