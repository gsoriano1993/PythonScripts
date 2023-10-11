#!/usr/bin/env python
# coding: utf-8

# In[1]:


PERIODO='20230912'
PERIODO_HASTA='20231003'


# In[2]:


get_ipython().run_cell_magic('capture', '', '!pip install teradatasqlalchemy==17.0.0.5\n!pip install sqlalchemy==1.4.44\n!pip install scrapy\n')


# In[3]:


import pandas as pd
import datetime
import teradatasql
from sqlalchemy import create_engine,Table, Column, Integer, String, Float, MetaData, ForeignKey,  insert, inspect
import numpy as np
import matplotlib.pyplot as plt
import os
import os.path
from sqlalchemy import create_engine
import time
from dateutil.relativedelta import relativedelta
import gc
from datetime import date
from bs4 import BeautifulSoup
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches
import seaborn as sns
import pyodbc
import statistics as stat
import seaborn as sns
from scrapy.http import HtmlResponse


#from dotenv import load_dotenv
from ibm_watson_studio_lib import access_project_or_space
from ibm_watson_machine_learning import APIClient
from project_lib.utils import environment
wslib = access_project_or_space()
import re
# Conexion a teradata
td_engine = create_engine('teradatasql://l0341304:Customer199325.@galicia10n2.bancogalicia.com.ar/DBC?logmech=LDAP')
inspector = inspect(td_engine)
print(inspector)
import warnings
# Settings the warnings to be ignored
warnings.filterwarnings('ignore')


# In[4]:


# Datos del proyecto
from project_lib import Project
PROJECT_ID = os.environ.get('PROJECT_ID')
TOKEN = os.environ.get('USER_ACCESS_TOKEN')

project = Project(
    project_id = PROJECT_ID,
    project_access_token = TOKEN)

# Acceso al proyecto
from ibm_watson_studio_lib import access_project_or_space
wslib = access_project_or_space()

# Seteo el display
pd.set_option("display.max_columns", 15)
pd.set_option("display.max_rows", 15)
pd.options.display.float_format = '{:.6f}'.format
url = environment.get_common_api_url()

# user access token
token = os.environ['USER_ACCESS_TOKEN']

# wml credentials
wml_credentials = {
     "instance_id": "openshift",
     "token": token,
     "url": url,
     "version": "4.5"
}

# wml client
client = APIClient(wml_credentials)

project_name = os.getenv('PROJECT_NAME')
wslib.show(project_name)
project_id = wslib.here.get_ID()
wslib.show(project_id)
client.set.default_project(project_id)


# In[5]:


# Funcion para levantar nombres de los 2000 clientes con nombres mas repetidos

select = '''
select top 3000
case when instr(nombre , ' ',1,1)=0 then nombre
when instr(nombre , ' ',1,1)>0 then left(nombre,cast(instr(nombre , ' ',1,1) as int)-1) else null end as nombre_1, count(1) as q
from  p_dw_explo.party_idemog
where nombre_1 is not null 
and nombre_1 <>''
and lower(nombre_1) not in ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')
group by 1
order by 2 desc
'''
con=td_engine.connect()
con.execute(select)
df_nombre = pd.DataFrame()
temp = pd.read_sql(select, con)
df_nombre = pd.concat((df_nombre, temp), ignore_index=True)
df_nombre = df_nombre.rename(columns=str.lower)


# In[6]:


df_nombre.rename(columns={"nombre_1":"nombre"}, inplace=True)


# In[7]:


# Funcion para levantar apellidos (idem logica que nombres)

select = '''
select top 2000
case when instr(apellido , ' ',1,1)=0 then apellido
when instr(apellido , ' ',1,1)>0 then left(apellido,cast(instr(apellido , ' ',1,1) as int)-1) else null end as apellido_1, count(1) as q
from  p_dw_explo.party_idemog
where apellido_1 is not null 
and apellido_1 <>''
and lower(apellido_1) not in ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')
group by 1
order by 2 desc
'''
con=td_engine.connect()
con.execute(select)
df_apellido = pd.DataFrame()
temp = pd.read_sql(select, con)
df_apellido = pd.concat((df_apellido, temp), ignore_index=True)
df_apellido = df_apellido.rename(columns=str.lower)


# In[8]:


df_apellido.rename(columns={"apellido_1":"apellido"}, inplace=True)


# In[9]:


query_direcciones='''
select top 2000 
street, count(1) as q
from p_dw_explo.party_domicilio
where street <>''
and street is not null
and street <>'AAAA'
and length(street) >3
group by 1
order by 2 desc
'''

con=td_engine.connect()
con.execute(query_direcciones)
df_direcciones = pd.DataFrame()
temp = pd.read_sql(query_direcciones, con)
df_direcciones = pd.concat((df_direcciones, temp), ignore_index=True)
df_direcciones = df_direcciones.rename(columns=str.lower)


# In[10]:


query_mensajes=f'''
select 
caso_id , cast(fecha_ts as date) as fecha, m.mensaje_id, m.cuerpo_mensaje_tx
from p_dw_explo.SMCC_MENSAJES m
left join p_dw_explo.SMCC_MENSAJES_segmentos ms on m.mensaje_id=ms.mensaje_cd
left join  p_lk_explo.SMCC_CASOS_MENSAJES casm
on m.mensaje_id=casm.mensaje_id
left join p_dw_explo.smcc_casos cas
on casm.caso_id=cas.case_cd
left join p_lk_explo.smcc_colas c
on ms.encolado_cd=c.cola_cd
where to_char(fecha_insertada_ts,'yyyymmdd') between {PERIODO} and {PERIODO_HASTA}
AND c.nombre_tx IN ('Bonos y Acciones', 'Reclamos/Solicitudes - SA', 'Whatsapp - SA','Banco Galicia Facebook','Twitter','Chat BG.com','Whatsapp','Chat Retenciones','Chat Onb','Mail Banco Galicia','
Mail Eminent','Mail Galicia Move','Seguridad','Instagram Eminent','Instagram Banco Galicia','Instagram Move','Mail Inversiones_BGBA','SPA - Derivador','Seccion de Ayuda','Experimento',
'Chat Empresas', 'Comercios', 'Mail ArchivoGo','Mail CentroDeAyuda', 'Mail Galicia Move', 'Mail GoClientes', 'Mail GoNoClientes')
AND agrupado_por_mensaje_cd is null'''

con=td_engine.connect()
con.execute(query_mensajes)
df_mensajes = pd.DataFrame()
temp = pd.read_sql(query_mensajes, con)
df_mensajes = pd.concat((df_mensajes, temp), ignore_index=True)
df_mensajes = df_mensajes.rename(columns=str.lower)


# In[11]:


df_mensajes


# In[12]:


#Limpiamos caracteres desconocidos de los mensajes y luego unimos los mensajes que corresponden a un unico caso en solo una celda
x=''
df_nuevo=pd.DataFrame()
df_nuevo["caso_id"]=df_mensajes["caso_id"].unique()
df_nuevo["mensaje"]=''
j=0
for i in df_nuevo["caso_id"]:
    x=df_mensajes.loc[df_mensajes["caso_id"]==i, "cuerpo_mensaje_tx"]
    df_nuevo["mensaje"][j]=x.str.cat(sep=". ").replace('�','')
    j=j+1


# In[13]:


query_etiquetas=f'''
select to_number(caso_id ) as codigo_del_caso, tiposubtipo from 
sbx_ccc.vw_Core_Contactos_Total_v3_0_0 cc
where 1=1
and registracion='EtiquetaYoizen'
and to_char(fecha_contacto, 'yyyymmdd') between {PERIODO} and {PERIODO_HASTA}
'''
con=td_engine.connect()
con.execute(query_etiquetas)
df_etiquetas = pd.DataFrame()
temp = pd.read_sql(query_etiquetas, con)
df_etiquetas = pd.concat((df_etiquetas, temp), ignore_index=True)
df_etiquetas = df_etiquetas.rename(columns=str.lower)


# In[14]:


#df_etiquetas=df_etiquetas.loc[~df_etiquetas.codigo_del_caso.isin(df_nuevo["caso_id"].to_list()), ["codigo_del_caso","agrupador","etiqueta","subetiqueta"]].reset_index(drop=True)


# In[15]:


'''i=0
df_etiquetas["etiqueta_unida"]=''
for i in range(0, len(df_etiquetas)):
    df_etiquetas["etiqueta_unida"][i]=str(df_etiquetas.agrupador[i])+' > '+str(df_etiquetas.etiqueta[i])+' > '+str(df_etiquetas.subetiqueta[i])
df_etiquetas.etiqueta_unida=df_etiquetas.etiqueta_unida.str.replace('> None','')
'''


# In[ ]:





# In[16]:


'''x=''
df_nuevo_etiquetas=pd.DataFrame()
df_nuevo_etiquetas["caso_id"]=df_etiquetas["codigo_del_caso"].unique()
df_nuevo_etiquetas["etiqueta_final"]=''
j=0
for i in df_nuevo_etiquetas["caso_id"]:
    x=df_etiquetas.loc[df_etiquetas["codigo_del_caso"]==i, "etiqueta_unida"]
    df_nuevo_etiquetas["etiqueta_final"][j]=x.str.cat(sep="; ")
    j=j+1
'''


# In[17]:


df_mensajesAux=pd.merge(df_etiquetas, df_nuevo, left_on="codigo_del_caso", right_on="caso_id", how = "inner").copy()


# In[18]:


df_mensajesAux.rename(columns={"mensaje":"cuerpo_mensaje_tx", "caso_id":"mensaje_id"}, inplace=True)


# In[19]:


df_mensajesAux=df_mensajesAux[["mensaje_id", "tiposubtipo", "cuerpo_mensaje_tx"]]


# In[20]:


df2=df_mensajesAux.copy()


# In[21]:


df_etiquetas.shape


# In[22]:


#creamos la funcion parserMensajes que va a recibir un texto para limpiar el codigo HTML
def parserMensajes(i):
    noHtml = []
    soup = BeautifulSoup(str(i).replace('>','> '))
    noHtml.append(soup.get_text())
    return noHtml


# In[23]:


#Creamos una funcion listaLimpia que vaya guardando cada mensaje_id y el texto del msj sin el codigo HTML
listaLimpia = []
for x in range(1,df2.shape[0]):
    v_mensaje_id=df2.iloc[x:x+1].mensaje_id.tolist()
    emails = df2.iloc[x:x+1].cuerpo_mensaje_tx.tolist()
    v_mensaje_limpio=parserMensajes(emails)
    listaLimpia.append([v_mensaje_id ,v_mensaje_limpio])


# In[24]:


#Convertimos la lista en un dataframe y le asignamos los nombres de columna correspondiente
df6 = pd.DataFrame(listaLimpia, columns=["mensaje_id", "cuerpo_mensaje_tx"])


# In[25]:


#Removemos los primeros corchetes ya que teniamos una lista de listas
df6["mensaje_id"]=df6["mensaje_id"].str[0]
df6.cuerpo_mensaje_tx=df6.cuerpo_mensaje_tx.str[0]


# In[26]:


#Removemos la segunda linea de corchetes para que quede el texto limpio
df6.cuerpo_mensaje_tx=df6.cuerpo_mensaje_tx.str.replace("'", " ")
df6.cuerpo_mensaje_tx=df6.cuerpo_mensaje_tx.str.strip('[')
df6.cuerpo_mensaje_tx=df6.cuerpo_mensaje_tx.str.strip(']')
#removemos saltos de linea (literales) y caracteres raros
df6.replace(r'\\n', " ", regex=True, inplace=True)
df6.replace(r'\\r', " ", regex=True, inplace=True)
df6.replace(r'\\xa0', " ", regex=True, inplace=True)
df6.replace(r'\\xa0', " ", regex=True, inplace=True)
df6.replace(r'\\x1a Â', " ", regex=True, inplace=True)
df6.replace(r'\\x1a', " ", regex=True, inplace=True)
#Corregimos palabras con acento
df6.replace(r'Ã¡', "á", regex=True, inplace=True)
df6.replace(r'Ã©', "é", regex=True, inplace=True)
df6.replace(r'Ã-', "í", regex=True, inplace=True)
df6.replace(r'Ã³', "ó", regex=True, inplace=True)
df6.replace(r'Ãº', "ú", regex=True, inplace=True)
df6.replace(r'Ã±', "ñ", regex=True, inplace=True)


# In[27]:


df_mensajesAux['mensaje_id'] = df_mensajesAux['mensaje_id'].astype(str)


# In[28]:


df6['mensaje_id'] = df6['mensaje_id'].astype(str)


# In[29]:


#Joineamos el df con el texto limpio con el original para tener caso, cola y orden de msj
df7=df6.merge(df_mensajesAux, how="inner", on="mensaje_id")


# In[30]:


df7


# In[31]:


#Dejamos en un dataframe final la info joineada y los campos seleccionados haciendole una foto al df joineado anteriormente
dfFinal=df7[[ 'mensaje_id', 'cuerpo_mensaje_tx_x', 'tiposubtipo']].copy()


# In[32]:


dfFinal.replace(r'\xa0', " ", regex=True, inplace=True)
dfFinal.replace(r'\u200c', " ", regex=True, inplace=True)
dfFinal.replace(r'\\t', " ", regex=True, inplace=True)


# In[33]:


dfFinal


# In[34]:


dfFinal= dfFinal.rename(columns={"cuerpo_mensaje_tx_x":"cuerpo_mensaje_tx"})


# In[35]:


dfaux=pd.DataFrame()
dfaux=dfFinal.copy()
#dfaux=pd.concat([df_mensajes,dfFinal]).copy()


# In[36]:


dfaux=dfaux.copy().reset_index(drop=True)
#del dfaux


# In[37]:


patron_saltos_de_linea=re.compile("\\n", re.IGNORECASE)
patron_saltos_de_linea2=re.compile("\\r", re.IGNORECASE)


# In[38]:


for i in range (0,len(dfaux)):
    dfaux["cuerpo_mensaje_tx"][i]=re.sub(patron_saltos_de_linea, "",dfaux["cuerpo_mensaje_tx"][i])
    dfaux["cuerpo_mensaje_tx"][i]=re.sub(patron_saltos_de_linea2, "",dfaux["cuerpo_mensaje_tx"][i])


# In[39]:


#excluimos nombres y apellidos con longitud menor a 3 caracteres
df_nombre=df_nombre.loc[df_nombre.nombre.apply(len)>3]
df_apellido=df_apellido.loc[df_apellido.apellido.apply(len)>3]


# In[40]:


#limpiamos del dataframe de nombres los apellidos que se colaron ahi
df_cruce=pd.merge(df_nombre, df_apellido, how="inner", left_on="nombre", right_on="apellido")
df_nombre=df_nombre.loc[~df_nombre["nombre"].isin(df_cruce.nombre.to_list())]


# In[41]:


#excluimos nombres que no corresponden borrarse
df_nombre.drop(df_nombre[df_nombre["nombre"]=="ARGENTINA"].index, inplace=True)
df_nombre.drop(df_nombre[df_nombre["nombre"]=="BANCO"].index, inplace=True)
df_nombre.drop(df_nombre[df_nombre["nombre"]=="DIAS"].index, inplace=True)
df_nombre.drop(df_nombre[df_nombre["nombre"]=="VALOR"].index, inplace=True)
df_nombre.drop(df_nombre[df_nombre["nombre"]=="MERCADO"].index, inplace=True)
df_nombre.drop(df_nombre[df_nombre["nombre"]=="GALA"].index, inplace=True)

df_apellido.drop(df_apellido[df_apellido["apellido"].str.lower()=="argentina"].index, inplace=True)
df_apellido.drop(df_apellido[df_apellido["apellido"].str.lower()=="banco"].index, inplace=True)
df_apellido.drop(df_apellido[df_apellido["apellido"].str.lower()=="dias"].index, inplace=True)
df_apellido.drop(df_apellido[df_apellido["apellido"].str.lower()=="valor"].index, inplace=True)
df_apellido.drop(df_apellido[df_apellido["apellido"].str.lower()=="mercado"].index, inplace=True)
df_apellido.drop(df_apellido[df_apellido["apellido"].str.lower()=="gala"].index, inplace=True)
df_direcciones.drop(df_direcciones[df_direcciones["street"].str.lower()=="galicia"].index, inplace=True)


# In[42]:


lista_nombres=[]
lista_nombres=df_nombre.nombre.str.lower().to_list()
lista_apellidos=[]
lista_apellidos=df_apellido.apellido.str.lower().to_list()
lista_direcciones=[]
lista_direcciones=df_direcciones.street.str.lower().to_list()


# In[43]:


df_resultados=pd.DataFrame()
df_resultados=dfaux.copy().reset_index(drop=True)


# In[ ]:





# In[44]:


df_resultados


# In[45]:


x=''
ediciones=[]
for i in range(0, len(df_resultados)):
    #reemplazamos letras con acento por sin acento
    x=df_resultados["cuerpo_mensaje_tx"][i].replace('ó', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ú', 'u').replace('ñ', 'ni')
    ediciones.append(x)
df_resultados["cuerpo_mensaje_tx_editado"]=np.array(ediciones)


# In[46]:


patron_nombre=''
patron=''
res=''
res = "\\b|\\b".join([str(item) for item in lista_nombres])
patron_nombres='\\b'+res+'\\b'
patron_nombres_ok=re.compile(patron_nombres, re.IGNORECASE)

patron_numero=''
patron_numero='[0-9]|\\bcero\\b|\\buno\\b|\\bdos\\b|\\btres\\b|\\bcuatro\\b|\\bcinco\\b|\\bseis\\b|\\bsiete\\b|\\bocho\\b|\\bnueve\\b|\\bdiez\\b'
patron_numero_ok=re.compile(patron_numero, re.IGNORECASE)

patron_apellido=''
patron=''
res=''
res = "\\b|\\b".join([str(item) for item in lista_apellidos])
patron_apellidos='\\b'+res+'\\b'
patron_apellidos_ok=re.compile(patron_apellidos, re.IGNORECASE)

patron_direcciones=''
patron=''
res=''
res = "\\b|\\b".join([str(item) for item in lista_direcciones])
patron_direcciones='\\b'+res+'\\b'
patron_direcciones_ok=re.compile(patron_direcciones, re.IGNORECASE)

patron_cadena= re.compile('(el lun)\\b(.*)|(el mar)\\b(.*)|(el mie)\\b(.*)|(el jue)\\b(.*)|(el vie)\\b(.*)|(el sab)\\b(.*)|(el dom)\\b(.*)', re.IGNORECASE)

#patron_mail=re.compile('([A-Za-z0-9]+[.-_])*[A-Za-z0-9](@)', re.IGNORECASE)
patron_mail=re.compile('\S+@\S+',re.IGNORECASE)


# In[47]:


x=''
lista_resu_ok=[]
resu_regex="{NOMBRE} "
resu_regex_direc="{DIRECCION} "
resu_regex_mail="{MAIL} "
resu_regex_nro =str(np.random.randint(1, 9))

dict_resu=dict(zip(df_resultados.mensaje_id, df_resultados.cuerpo_mensaje_tx_editado))


# In[48]:


for msj in dict_resu.values():
    x=re.sub(patron_cadena,'',str(msj))
    x=re.sub(patron_nombres_ok,resu_regex , x)
    x=re.sub(patron_mail,resu_regex_mail , x)
    x=re.sub(patron_direcciones,resu_regex_direc , x)
    x=re.sub(patron_apellidos_ok, resu_regex, x )
    x=re.sub(patron_numero_ok, resu_regex_nro , x)
    lista_resu_ok.append(x)


# In[ ]:





# In[49]:


df_resultados["cuerpo_mensaje_encriptado"]=np.array(lista_resu_ok)


# In[50]:


df_resultados


# In[51]:


#volvemos a dejar bien los nombres

df_resultados.rename(columns={"mensaje_id":"caso_id"}, inplace=True)
df_resultados.rename(columns={"tiposubtipo":"etiqueta"}, inplace=True)


# In[52]:


df_resultados=df_resultados[["caso_id", "cuerpo_mensaje_tx", "cuerpo_mensaje_encriptado", "etiqueta" ]]


# In[53]:


df_resultados


# In[ ]:





# In[ ]:





# In[ ]:





# Exportamos a CSV

# In[54]:


from ibm_watson_studio_lib import access_project_or_space
from ibm_watson_machine_learning import APIClient
from project_lib.utils import environment
wslib = access_project_or_space()
# Datos del proyecto
from project_lib import Project
PROJECT_ID = os.environ.get('PROJECT_ID')
TOKEN = os.environ.get('USER_ACCESS_TOKEN')

 

project = Project(
    project_id = PROJECT_ID,
    project_access_token = TOKEN)

 

# Acceso al proyecto
from ibm_watson_studio_lib import access_project_or_space
wslib = access_project_or_space()

 

# Seteo el display
pd.set_option("display.max_columns", 15)
pd.set_option("display.max_rows", 15)
pd.options.display.float_format = '{:.6f}'.format


# In[55]:


carpeta = ''
archivo = "resultados_encriptacion_20230912_20231003.csv"
ruta_mul = os.path.join(carpeta, archivo)
project.save_data(data=df_resultados.to_csv(sep='|', index=False), file_name=ruta_mul, overwrite=True)


# In[64]:


len(re.findall("{NOMBRE} ", df_resultados["cuerpo_mensaje_encriptado"][0]))


# In[ ]:


suma_nombres=0
contador_filas_nombres=0
for i in range(0, len(df_resultados)):
    suma_nombres=len(re.findall("{NOMBRE} ", df_resultados["cuerpo_mensaje_encriptado"][i]))+suma_nombres
    if (len(re.findall("{NOMBRE} ", df_resultados["cuerpo_mensaje_encriptado"][i])) >0):
         contador_filas_nombres=contador_filas_nombres+1
"La tasa de nombres/apellidos encriptados por mensaje es: "+str(round(suma_nombres/contador_filas_nombres,3))


# In[ ]:


suma_mails=0
contador_filas_mails=0
for i in range(0, len(df_resultados)):
    suma_mails=len(re.findall("{MAIL} ", df_resultados["cuerpo_mensaje_encriptado"][i]))+suma_mails
    if (len(re.findall("{MAIL} ", df_resultados["cuerpo_mensaje_encriptado"][i])) >0):
         contador_filas_mails=contador_filas_mails+1
"La tasa de mails encriptados por mensaje es: "+str(round(suma_mails/contador_filas_mails,3))


# In[ ]:


suma_direcciones=0
contador_filas_direcciones=0
for i in range(0, len(df_resultados)):
    suma_direcciones=len(re.findall("{DIRECCION} ", df_resultados["cuerpo_mensaje_encriptado"][i]))+suma_direcciones
    if (len(re.findall("{DIRECCION} ", df_resultados["cuerpo_mensaje_encriptado"][i])) >0):
         contador_filas_direcciones=contador_filas_direcciones+1
"La tasa de direcciones encriptados por mensaje es: "+str(round(suma_direcciones/contador_filas_direcciones,3))

