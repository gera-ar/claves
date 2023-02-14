# Keys

[Gerardo Kessler](http://gera.ar)  

Este programa es un gestor de contraseñas sencillo para Windows programado en [Python](https://python.org)  

La seguridad se basa en la encriptación de la base de datos a través de un archivo clave único. No tiene conexión a internet, por lo que los datos solo se almacenan de forma local para evitar una posible pérdida de datos.

## Primera ejecución

Al ejecutarse por primera  vez se solicita la creación  de un archivo clave. Este va a estar asociado a la contraseña de acceso y a la base de datos, por lo que es muy importante guardar una copia del archivo en lugar seguro. La pérdida del archivo clave implica la imposibilidad de acceso a los datos guardados

Seguidamente se solicita una contraseña de acceso. Esta debe recordarse ya que no es posible restaurarla. Una vez creada, ya estaremos dentro de la interfaz en la que tan solo hay una entrada de muestra.

## Descripción de la interfaz

El primer elemento de la interfaz es la lista de entradas de la base de datos, la cual podemos recorrer con flechas arriba y abajo.

Tabulando aparecen los botones para las diferentes acciones:

* Modificar; Activa una ventana que muestra los diferentes campos editables para realizar las modificaciones. Al pulsar guardar se actualizan los datos en la base de datos.
* Eliminar; Elimina la entrada seleccionada en la lista.
* Añadir: Activa una ventana para ingresar los distintos campos y guardarlos como nueva entrada en la base de datos.
* Cerrar; Cierra el programa.

## Atajos de teclado de la lista

Desde la lista tenemos algunos comandos, a saber:

* Suprimir; Elimina el elemento enfocado en la lista.
* Control + c; Copia la contraseña del elemento enfocado al portapapeles.
* Control + u; Copia el nombre de usuario del elemento seleccionado al portapapeles.
* Control + e; Verbaliza la posición actual y el total de entradas en la lista.
* Barra espaciadora; Activa una ventana donde se muestran los datos ingresados en los diferentes campos. (No editable).
* Escape; Cierra el programa.

Asimismo se pueden activar los botones de la interfaz con sus correspondientes atajos desde cualquier enfoque en la ventana.

* Alt + m; Modificar
* Alt + e; Eliminar
* Alt + a; Añadir
* Alt + e, Cerrar

## Barra de menú

Pulsando la tecla alt en la ventana principal, podremos recorrer las opciones del menú archivo con flechas arriba y abajo;

* Exportar base de datos actual; Permite hacer una copia de seguridad de la base de datos encriptada.
* Importar base de datos existente; Permite importar una base de datos ya creada para ser utilizada con el programa. (Para utilizar una base de datos existente, es necesario tener el archivo clave asociado a esa base de datos).
* Cambiar la contraseña de acceso; Permite cambiar la contraseña de acceso al programa.
* Exportar archivo clave; Permite hacer una copia de seguridad del archivo clave.

### Errores

Si el archivo clave se corrompe o se elimina, al volver a iniciarse el ejecutable se va a solicitar buscar ese archivo con un diálogo típico de Windos. En el caso de tener una copia se guarda en la configuración la nueva ruta del archivo. De lo contrario hay que eliminar el archivo de configuración y la base de datos para volver a iniciar el programa con una nueva base de datos.

Si el programa fué cerrado de forma incorrecta, al volver a ejecutarlo es posible que aparezca un cartel de aviso que informa que ya existe una instancia activa del programa.

Para solucionar este problema el diálogo ofrece restaurar los archivos volviendo a encriptar la base de datos. Si efectivamente existe una instancia activa, no es conveniente utilizar la opción restaurar para evitar conflictos de lectura.

