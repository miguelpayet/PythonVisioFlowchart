from funciones import SetValor
from collections import defaultdict
from collections import OrderedDict
from resolvedor import Resolvedor
        

class Dependencia:

    def __init__(self, t, n):
        self.tipo = t
        self.nombre = n

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.nombre + " (" + self.tipo + ")"


class GrupoRecursos:

    def __init__(self):
        self.recursos = defaultdict(dict)

    def agregarRecurso(self, recurso):
        self.recursos[recurso.tipo][recurso.id] = recurso

    def crearArbol(self):
        for tipo,recursos in self.recursos.items():
            for k,v in recursos.items():
                for d in v.dependencias:
                    if d.tipo in self.recursos:
                        if d.nombre in self.recursos[d.tipo]:
                            self.recursos[d.tipo][d.nombre].agregarDependiente(v)
                        else:
                            print ("error de nombre que no existe ", ' -> ', d)
                    else:
                        print ("error de tipo que no existe ", ' -> ', d)

    def recursosConHijos(self):
        todos = self.todosLosRecursos()
        todosConHijos = []
        for r in todos:
            if r.totalDependencias() == 0 and r.totalDependientes() > 0: 
                todosConHijos.append(r)
        return todosConHijos

    def recursosSinHijos(self):
        todos = self.todosLosRecursos()
        todosSinHijos = []
        for r in todos:
            if r.totalDependencias() == 0 and r.totalDependientes() == 0: 
                todosSinHijos.append(r)
        return todosSinHijos
    
    def todosLosRecursos(self):
        todos = []
        for recdict in self.recursos.values():
            for rec in recdict.values():
                todos.append(rec)
        return todos


class Recurso:

    def __init__(self, r, parameters):
        self.nivel = 0
        self.apiVersion = ""
        self.dependencias = []
        self.dependientes = []
        self.displayName = ""
        self.id = ""
        self.nombre = ""
        self.sku = ""
        self.tipo = ""
        self.vmSize = ""
        self.resolvedor = Resolvedor(parameters)
        self.setNombre(r)
        self.setTipo(r)
        self.setApiVersion(r)
        self.setVmSize(r)   
        self.setDisplayName(r)
        self.calcularDependencias(r, parameters)

    def __eq__(self, other):
        return self.nombre == other.nombre

    def __gt__(self, other):
        return self.nombre > other.nombre

    def __lt__(self, other):
        return self.nombre < other.nombre

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.nombre + " (" + self.tipo + ")"
        
    def agregarDependiente(self, dependiente):
        if (self.tipo == "Microsoft.Compute/availabilitySets") and (dependiente.tipo == "Microsoft.Compute/virtualMachines"):
            pass
        else:
            self.dependientes.append(dependiente)

    def calcularDependencias(self, r, parameters):
        if "dependsOn" in r:
            for d in r["dependsOn"]:
                nombre = self.limpiarNombre(d)
                deps = self.resolvedor.resolver(nombre)  
                for d in deps[1]:
                    self.dependencias.append(Dependencia(deps[0], d))

    def calcularNombre(self, n):
        nombre = self.limpiarNombre(n)
        cadena = self.resolvedor.resolver(nombre)         
        return cadena
    
    def dibujar(self, visio, nivelHorizontal, nivelVertical, shapePadre = None):
        primero = True
        item = visio.obtenerShape(self.tipo)
        if item == None:
            print("item ", self.tipo, " no existe en stencil")
        else:
            x = nivelHorizontal
            shape = visio.dropShape(item, x, visio.y, self.displayName)
            nivelHorizontal += 1
            x = 1.2 * nivelHorizontal
            if shapePadre is not None:
                shapePadre.autoConnect(shape, 0)
            if self.totalDependientes() > 0:
                for d in self.dependientes:
                    if not primero:
                        visio.y -= 0.9
                    else:
                        primero = False
                    d.dibujar(visio, nivelHorizontal, nivelVertical, shape)
        return 0

    def limpiarNombre(self, nombre):
        nombre = nombre[1:len(nombre) - 1]
        return nombre
        
    def nombreAbreviado(self):
        lista = self.tipo.rpartition("/")
        nombre = self.nombre + " (" + lista[2] + ")"
        return nombre
    
    def obtenerArbol(self, parent):
        self.nivel += 1
        lista = OrderedDict()
        if self.totalDependientes == 0:
            lista[self.__str__()] = {}
            return lista
        for d in self.dependientes:
            if d == parent:
                lista["referencia circular a " + parent.__str__()] = {}
            else:
                lista[d.__str__()] = d.obtenerArbol(self)            
        self.nivel -= 1
        return lista

    def setApiVersion(self, r):
        self.apiVersion = SetValor(r, "apiVersion")

    def setDisplayName(self, r):
        valor = None
        if "properties" in r:
            if "displayName" in r["properties"]:
                valor = r["properties"]["displayName"]
        if valor is None:
            self.displayName = self.nombreAbreviado()
        else:
            if valor[0] == "[":
                valor = self.limpiarNombre(valor)
            else:
                valor = '"' + valor + '"'
                self.displayName = self.resolvedor.resolver(valor)
        
    def setNombre(self, r):
        self.nombre = self.calcularNombre(r["name"])
        lista = self.nombre.rpartition("/")
        self.id = lista[2]

    def setSKU(self, r):
        if "sku" in r:
            sku = r["sku"]
            self.sku = SKU()
            self.sku.name = SetValor(sku, "name")
            self.sku.capacity = SetValor(sku, "capacity")
            self.sku.tier = SetValor(sku, "tier")
        else:
            self.sku = None 

    def setTipo(self, r):
        self.tipo = SetValor(r, "type")

    def setVmSize(self, r):
        self.vmSize = ""
        if "properties" in r:
            if "hardwareProfile" in r["properties"]:
                if "vmSize" in r["properties"]["hardwareProfile"]:
                    self.vmSize = r["properties"]["hardwareProfile"]["vmSize"]

    def totalDependencias(self):
        return len(self.dependencias)

    def totalDependientes(self):
        return len(self.dependientes)


class RecursoError(Recurso):
    
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre

class SKU:

    name = ""
    capacity = ""
    tier = ""
