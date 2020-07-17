from PySan.Base.Route import Route

Route = Route()
route_config = [
    Route.route('/', 'site/site@index'),
    Route.route('/tes', 'ggg/ggg@index')
]