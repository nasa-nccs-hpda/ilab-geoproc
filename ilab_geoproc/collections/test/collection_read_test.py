from geoproc.collections.collection import Collection

collectionName = "merra_daily_local_test1"
collection = Collection.new(collectionName)
print( collection )

var = collection.getVariable("t")
print( var )