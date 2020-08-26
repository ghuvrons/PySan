import datetime
import PySan.Database.MySQL.Query as Query
class ListOfModels():
    def __init__(self, models = []):
        self.models = models
    def append(self, model):
        self.models.append(model)
    def __len__(self):
        if type(self.models) in [list, dict]:
            return len(self.models)
        return 0
    def __setitem__(self, i, val):
        self.models[i] = val
    def __getitem__(self, table):
        return self.models[table]

class ModelsAsObject(object):
    def __init__(self, obj_class, key, models = [], parent = None, on = {}):
        self.__attributtes = {}
        self.__obj_class = obj_class
        self.__key = key
        self.__parent = parent
        self.__on = on
        for m in models:
            self.__attributtes[getattr(m, key)] = m
    def __getitem__(self, name):
        if not self.__attributtes.has_key(name):
            args = {self.__key: name}
            for key in self.__on.keys():
                if self.__parent is not None:
                    args[self.__on[key]] = getattr(self.__parent, key)
            print args
            self.__attributtes[name] = self.__obj_class.create(**args)
        return self.__attributtes[name]
    def save(self):
        for key in self.__attributtes.keys():
            self.__attributtes[key].save()

class Model(object):
    DB = None
    TABLE = None

    def __init__(self):
        self._primary_key = "id"
        self.__id = None
        self.__updated__attr = {}
        self.__attributtes = self._attributtes()
        self.__relations = {}
        self.__generate__attrs()

    @classmethod
    def create(this_class, *arg, **args):
        model = this_class()
        for key in args.keys():
            setattr(model, key, args[key])
        return model

    @classmethod
    def createFromDict(this_class, args, is_new = True):
        model = this_class()
        for key in args.keys():
            # if key in attrs:
            setattr(model, str(key), args[key])
        if not is_new:
            model.__updated__attr = {}
            if model._primary_key in args.keys():
                model.__id = args[model._primary_key]
        return model

    @classmethod
    def one(this_class, *arg, **args):
        db = this_class.Databases[this_class.DB]
        _where = []
        for key in args.keys():
            _where.append((key, args[key], ))
        results = db[this_class.TABLE].select(asDictionary = True, 
            where=_where, 
            limit=1
        )
        model = None
        for r in results:
            model = this_class.createFromDict(r, False)
        return model

    @classmethod
    def all(this_class):
        db = this_class.Databases[this_class.DB]
        results = db[this_class.TABLE].select(asDictionary = True)
        models_list = []
        for r in results:
            model = this_class.createFromDict(r, False)
            models_list.append(model)
        return models_list
        
    @classmethod
    def search(this_class, *arg, **args):
        db = this_class.Databases[this_class.DB]
        _where = []
        for key in args.keys():
            _where.append((key, args[key], ))
        results = db[this_class.TABLE].select(asDictionary = True, 
            where=_where
        )
        models_list = []
        for r in results:
            model = this_class.createFromDict(r, False)
            models_list.append(model)
        return models_list
    
    def _attributtes(self):
        return {}

    def __setattr__(self, name, value):
        if (hasattr(self, "_Model__attributtes") 
         and self.__attributtes.has_key(name) 
         and self.__attributtes[name].has_key("datatype")
        ):
            datatype = self.__attributtes[name]["datatype"]
            new_value = None
            if value is None:
                new_value = value
            elif datatype == 'int':
                new_value = int(value)
            elif datatype == 'float':
                new_value = float(value)
            elif datatype == 'str':
                new_value = str(value)
            elif datatype == 'unicode':
                new_value = unicode(value)
            elif datatype == 'date':
                if type(value) in [str, unicode]:
                    tmp_val = datetime.datetime.strptime(value, '%Y-%m-%d').date()
                elif type(value) is int:
                    tmp_val = datetime.date.fromtimestamp(value)
                elif type(value) is datetime.date:
                    tmp_val = value
                else:
                    tmp_val = None
                new_value = tmp_val
            elif datatype == 'list':
                new_value = value
            elif datatype == 'dict':
                new_value = value
            elif datatype == 'relation_has_one':
                new_value = value
            elif datatype == 'relation_has_many':
                new_value = value
            if datatype not in ['relation_has_one', 'relation_has_many', 'relation_as_object']:
                self.__updated__attr[name] = new_value
            return object.__setattr__(self, name, new_value)

        return object.__setattr__(self, name, value)
    def __getattribute__(self, name):
        if (name is not '_Model__attributtes'
         and hasattr(self, "_Model__attributtes") 
         and self.__attributtes.has_key(name) 
         and self.__attributtes[name].has_key("datatype")
        ):
            datatype = self.__attributtes[name]["datatype"]
            if datatype == 'relation_has_one':
                if object.__getattribute__(self, name) == None:
                    _on = self.__attributtes[name]["on"]
                    _class_model = self.__attributtes[name]["class_model"]
                    _where = {}
                    for key in _on.keys():
                        _where[_on[key]] = self.__id
                    model = _class_model.one(**_where)
                    object.__setattr__(self, name, model)
            elif datatype == 'relation_has_many':
                if object.__getattribute__(self, name) == None:
                    _on = self.__attributtes[name]["on"]
                    _class_model = self.__attributtes[name]["class_model"]
                    _where = {}
                    for key in _on.keys():
                        _where[_on[key]] = self.__id
                    models = _class_model.search(**_where)
                    object.__setattr__(self, name, ListOfModels(models))
            elif datatype == 'relation_as_object':
                if object.__getattribute__(self, name) == None:
                    _on = self.__attributtes[name]["on"]
                    _key = self.__attributtes[name]["key"]
                    _class_model = self.__attributtes[name]["class_model"]
                    _where = {}
                    for key in _on.keys():
                        _where[_on[key]] = self.__id
                    models = _class_model.search(**_where)
                    object.__setattr__(self, name, ModelsAsObject(_class_model, _key, models, 
                            parent=self, 
                            on=_on
                        )
                    )
        return object.__getattribute__(self, name)
    def __generate__attrs(self):
        _attrs = self.__attributtes
        if self._primary_key in _attrs.keys():
            _attrs[self._primary_key]['primary'] = True
        for _key in _attrs.keys():
            if _attrs[_key]["datatype"] == 'relation':
                self.__relations[_key] = {
                    "class_model":_attrs[_key]["class_model"],
                    "data": []
                }
            setattr(self, _key, _attrs[_key]["default"] if _attrs[_key].has_key("default") else None)
    def save(self):
        db = self.Databases[self.DB][self.TABLE]
        if self.__id is None:
            results = db.insert(self.__updated__attr)
        else:
            results = db.update(self.__updated__attr,
                where=[(self._primary_key, self.__id)]
            )
        print results.result

    @staticmethod
    def _integer(default = 0):
        return {
            "datatype" : "int",
            "default": int(default)
        }

    @staticmethod
    def _float(default = 0.0):
        return {
            "datatype" : "float",
            "default": float(default)
        }

    @staticmethod
    def _string(default = None):
        return {
            "datatype" : "str",
            "default": str(default) if default else None
        }

    @staticmethod
    def _unicode(default = None):
        return {
            "datatype" : "unicode",
            "default": unicode(default) if default else None
        }

    @staticmethod
    def _date(default = None):
        return {
            "datatype" : "date",
            "default": default
        }

    @staticmethod
    def _time(default = None):
        return {
            "datatype" : "time",
            "default": default
        }

    @staticmethod
    def _datetime(default = None):
        return {
            "datatype" : "datetime",
            "default": default
        }

    @staticmethod
    def _array(default = []):
        return {
            "datatype" : "list",
            "default": default
        }

    @staticmethod
    def _object(default = {}):
        return {
            "datatype" : "dict",
            "default": default
        }

    @staticmethod
    def _hasOne(class_model, on = {}):
        return {
            "datatype" : "relation_has_one",
            "class_model" : class_model,
            "on" : on,
            "default": None
        }
    
    @staticmethod
    def _hasMany(class_model, on = {}):
        return {
            "datatype" : "relation_has_many",
            "class_model" : class_model,
            "on" : on,
            "default": None
        }
    
    @staticmethod
    def _hasObject(class_model, on = {}, key="key"):
        return {
            "datatype" : "relation_as_object",
            "class_model" : class_model,
            "on" : on,
            "key" : key,
            "default": None
        }
    