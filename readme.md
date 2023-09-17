# Claves

[Gerardo Kessler](http://gera.ar)  

Este programa es un gestor de contraseñas sencillo para Windows programado en [Python](https://python.org)  

La seguridad se basa en el cifrado simétrico de los datos almacenados en la base de datos partiendo del hash de una contraseña personal del usuario.

## Primera ejecución

En el primer ingreso se solicita una contraseña de acceso. Esta debe ser segura y fácil de recordar ya que los datos se encriptan basados en la misma, y sin ella no se puede acceder a los datos almacenados.

## Diálogo de contraseña

En este diálogo inicial se solicita la contraseña configurada en la primera ejecución. Al pulsar intro o el botón ingresar se procede a la verificación.
Si la contraseña es la correcta se muestra la interfaz principal, de lo contrario se muestra un mensaje de error.  
A parte del botón ingresar también se encuentra un botón que permite resetear la base de datos para comenzar el proceso desde 0.

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
* Control + c; Copia la contraseña o fecha de vencimiento del elemento enfocado al portapapeles.
* Control + u; Copia el nombre de usuario o número de tarjeta del elemento seleccionado al portapapeles.
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
* Importar base de datos existente; Permite importar una base de datos ya creada para ser utilizada con el programa. (Para utilizar una base de datos existente, es necesaria la contraseña de acceso de los datos encriptados).
* Cambiar la contraseña de acceso; Permite cambiar la contraseña de acceso al programa.

