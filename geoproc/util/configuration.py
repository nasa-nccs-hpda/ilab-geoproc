

class ConfigurableObject:

    def __init__(self, **kwargs):
        self.parms = { **kwargs }

    def getParameter(self, name: str, **kwargs ):
        return kwargs.get( name, self.parms.get(name) )

    def setDefaults( self, **kwargs ):
        self.parms.update( kwargs )