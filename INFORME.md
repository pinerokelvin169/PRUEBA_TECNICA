# INFORME DE PRUEBA TÉCNICA A PASANTE DE SISTEMAS – YOBEL
## OPERACIONES CHARDON

**ESTUDIANTE:** Kelvin Jesús Piñero A.

**FECHA:** 05 de agosto de 2026

---

## A) Problemas de calidad que encontraste en el Excel

Lista cada uno, cuántas filas afecta, y qué decidiste hacer. Si decidiste no corregir algo, dilo y explica por qué.

- El primer problema al revisar la data "al ojo" fue que en muchos campos como el id_operacion tenía espacios en blanco. En cliente también había campos con este inconveniente. Aquí se aplicó la eliminación de espacios en blanco en ambos lados de los campos para evitar inconvenientes de correspondencia o sensibilidad.

- Las fechas de OP-2026-1019, OP-2026-1055, OP-2026-1088, OP-2026-1101, estaban en un formato que no corresponde al de la mayoría que en general, está de forma AAAA-MM-DD, utilizando "/" como separador en vez de usar "-". En estos campos se aplicó una estandarización al formato correspondiente que se mencionó anteriormente

- Los clientes de las operaciones OP-2026-1023, OP-2026-1071, se encuentran vacíos o con N/A como texto donde debería ir la razón social del mismo. 

- En los montos, los campos OP-2026-1012, OP-2026-1048, OP-2026-1077, los valores no se encontraban estandarizados con la coma como separador de miles y punto para decimales, para lo cual decidí eliminar la coma y solo usar el punto como separador de decimales. Esto causaba problema porque no estaba sumando esos valores. 

- En el estado no estaban normalizados, pues la operación OP-2026-1005 tenía "COMPLETADO" en mayúsculas totalmente. Aquí solo se aplicó normalización para evitar variabilidad en los datos que en teoría, deberían estar estandarizados.

- También es importante mencionar que la operación OP-2026-1042 tenía un monto negativo. Decidí mantenerlo porque podría ser una devolución o ajuste que se haya realizado.

- Finalmente, las operaciones OP-2026-1036 y OP-2026-1052 estaban duplicadas, aunque tenían datos de montos distintos, el ID generaría conflicto ya que este debe ser único.

---

## B) Resumen de las discrepancias contra la API

Cuántas y de qué tipo.

Al comparar los registros de la BD con la API, encontré las siguientes discrepancias:

- **14 diferencias en montos:** Algunas son solo de formato (1694.30 vs 1694.3) y aunque pudiera obviarse, considero que es importante mantenerlas. También hay 4 casos donde los montos son diferentes. Por ejemplo, OP-2026-1027 tiene $4,816.31 en BD pero $4,730.91 en API, una diferencia de $85.40.

- **3 operaciones en BD pero no en API:** OP-2026-1008, OP-2026-1057 y OP-2026-1099. Esto significa que la API no tiene estos registros.

- **3 diferencias en cliente:** OP-2026-1015 tiene espacios extras, y OP-2026-1023 y OP-2026-1071 están vacías en la BD pero la API tiene datos.

- **2 diferencias en estado:** OP-2026-1018 está "Pendiente" en BD pero "Rechazado" en API. OP-2026-1063 está "Completado" en BD pero "Pendiente" en API. Esta discrepancia es importante ya que me fue mencionada durante a entrevista, y es uno de los problemas que presenta la empresa con sus clientes.

- **2 diferencias en fecha:** OP-2026-1019 tiene 2026-07-01 en BD pero 2026-01-07 en API. OP-2026-1055 tiene 2026-08-01 en BD pero 2026-01-08 en API. Parece que los meses y días están invertidos.

- **2 operaciones en API pero no en BD:** OP-2026-2001 y OP-2026-2002 están en la API pero no llegaron a la base de datos.

---

## C) Responde estas cinco preguntas:

### 1. Encontraste una operación donde el monto del Excel y el de la API no coinciden. ¿Cuál de los dos está bien? Explica tu razonamiento.

Considero que la API tiene la información correcta, tomando en cuenta que es un sistema principal que recibe la información en tiempo rela, a diferencia del Excel que es un reporte que se genera a mano, mediante IA o automáticamente del sistema, con la diferencia que puede ser generado con retrasos de sincronización o errores en la programación.

### 2. El reporte llega todos los días a las 8am. Un día no llega. ¿Cómo se entera el sistema de que faltó?

Asumo que el sistema debe tener un sistema de alertas de que no se ha cargado el reporte diario. En este caso, se puede ajustar el script para que reconozca si el archivo necesario está en la carpeta asignada. 

### 3. El mes que viene el proveedor agrega una columna nueva al Excel sin avisar. ¿Qué le pasa a tu script? ¿Qué harías para que no te tome por sorpresa?

Mi script ya no funcionaría porque lee las columnas por posición. Si se agrega una columna nueva los índices se desalinearían y los datos irían a las columnas incorrectos. Para evitar esto, modificaría el script para leer por nombres de columna en vez de la posición, y obviamente tendría que validar que existan las columnas antes de procesar.

### 4. La API te devuelve solo los primeros 50 registros por llamada. ¿Cómo te das cuenta de que faltan datos?

Al comparar los totales ya me daría cuenta porque en la BD tiene por ejemplo 120 pero la API devuelve solo 50. Una opción seria verificar si la API tiene paginación para ver las siguientes 50.

### 5. ¿Qué parte del enunciado no te quedó clara, o qué supuesto tuviste que inventar para poder avanzar?

Tuve que asumir que los nombres de clientes que estaban vacíos o con N/A son válidos, también que el monto que estaba en negativo era un ajuste o devolución y no un error de tipeo, en la eliminación de duplicados asumí que el primero era el correcto, y finalmente, como mencioné antes, las diferencias en la API son errores de sincronización no de la base de datos.
