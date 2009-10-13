from django.core.exceptions import ImproperlyConfigured    
                                                           
def _importpath(path, error_text=None):                    
    """
    Import object by specified ``path``.
    If ``error_text`` is not None and import raise an error
    then will raise ImproperlyConfigured with user friendly text.
    """
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        return getattr(__import__(module, {}, {}, ['']), attr)
    except ImportError, error:
        if error_text is not None:
            raise ImproperlyConfigured('Error importing %s from %s: "%s"' % (error_text, path, error))
        else:
            raise error
                                                                                                      
def importpath(path, error_text=None):                                                                
    """                                                                                               
    Import value by specified ``path``.                                                               
    Value can be an object or an attribute of an object.                                              
    If ``error_text`` is not None and import raise an error                                           
    then will raise ImproperlyConfigured with user friendly text.                                     
    """                                                                                               
    result = None                                                                                     
    attrs = []                                                                                        
    exception = None                                                                                  
    while True:                                                                                       
        try:
            result = _importpath(path, error_text)                                                    
        except (ImportError, ImproperlyConfigured), e:                                                
            if exception is None:                                                                     
                exception = e                                                                         
            i = path.rfind('.')                                                                       
            attrs.insert(0, path[i+1:])                                                               
            path = path[:i]                                                                           
        else:                                                                                         
            break                                                                                     
    for attr in attrs:                                                                                
        if not hasattr(result, attr):                                                                 
            raise exception                                                                           
        result = getattr(result, attr)                                                                
    return result                                                                                     
