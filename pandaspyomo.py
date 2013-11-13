""" pandaspyomo: read data from coopr.pyomo models to pandas DataFrames

Pyomo is a GAMS-like model description language for mathematical
optimization problems. This module provides functions to read data from 
Pyomo model instances and result objects. Use list_entities to get a list
of all entities (sets, params, variables, objectives or constraints) inside a 
pyomo instance, before get its contents by get_entity (or get_entities).

Usage:
    import pandaspyomo as pdpo
    pdpo.list_entities(instance, 'var')
        [('EprOut', ['time', 'process', 'commodity', 'commodity']), ... 
         ('EprIn',  ['time', 'process', 'commodity', 'commodity'])]
    epr = pdpo.get_entities(instance, ['EprOut', 'EprInt'])
    ...
    
"""
__all__ = ["get_entity", "get_entities", "list_entities"]

import pandas as pd

def get_entity(instance, name):
    """ Return a DataFrame for an entity in model instance.
    
    Args:
        instance: a Pyomo ConcreteModel instance
        name: name of a Set, Param, Var, Constraint or Objective
        
    Returns:
        a single-columned Pandas DataFrame with domain as index
    """
    
    # retrieve entity, its type and its onset names
    entity = instance.__getattribute__(name)
    entity_type = get_entity_type(entity)
    labels = get_onset_names(entity)

    # extract values
    if entity_type == 'set':
        # Pyomo sets don't have values, only elements
        results = pd.DataFrame([(v, 1) for v in entity.value])
        
        # for unconstrained sets, the column label is identical to their index
        # hence, make index equal to entity name and append underscore to name 
        # (=the later column title) to preserve identical index names for both
        # unconstrained supersets 
        if not labels:
            labels = [name]
            name = name+'_'
            
    elif entity_type == 'parameter':
        if entity.dim() > 1:
            results = pd.DataFrame([v[0]+(v[1],) for v in entity.iteritems()])
        else:
            results = pd.DataFrame(entity.iteritems())
    else:
        # create DataFrame
        if entity._ndim > 1:
            # concatenate index tuples with value if entity has multidimensional indices v[0]
            results = pd.DataFrame([v[0]+(v[1].value,) for v in entity.iteritems()])
        else:
            # otherwise, create tuple from scalar index v[0]
            results = pd.DataFrame([(v[0], v[1].value) for v in entity.iteritems()])

    # check for duplicate onset names and append one to several "_" to make 
    # them unique
    if len(set(labels)) != len(labels):
        for k, label in enumerate(labels):
            if label in labels[:k]:
                labels[k] = labels[k] + "_"
        
    # name columns according to labels + entity name
    results.columns = labels + [name]
    results.set_index(labels, inplace=True)
    
    return results
    
def get_entities(instance, names):
    """ Return one DataFrame with entities in columns and a common index.
    
    Works only on entities that share a common domain (set or set_tuple), which
    is used as index of the returned DataFrame.
    
    Args:
        instance: a Pyomo ConcreteModel instance
        names: list of entity names (as returned by list_entities)
        
    Returns:
        a Pandas DataFrame with entities as columns and domains as index
    """
    
    df = pd.DataFrame()
    for name in names:
        other = get_entity(instance, name)
        
        if df.empty:
            df = other
        else:
            index_names_before = df.index.names
           
            df = df.join(other, how='outer')
        
            if index_names_before != df.index.names:
                print "Warning: column names of indices don't match!"
                df.index.names = index_names_before
        
    return df

def list_entities(instance, entity_type=None):
    """ Return list of sets, params, variables, constraints or objectives
    
    Args:
        instance: a Pyomo ConcreteModel object
        type: (optional) "set", "param", "variable", "constraint" or "objective"
    
    Returns:
        list of tuples with (entity name, [list onset names]) of given type.
        if no type is given, returns a dict of lists for each type
        
    Example:
        >>> list_entities(instance, 'var')
        [('EprOut', ['time', 'process', 'commodity', 'commodity']), ... 
         ('EprIn',  ['time', 'process', 'commodity', 'commodity'])]
    """
    if not entity_type:
        result = {}
        for entity_type in ['set', 'parameter', 'variable', 'constraint', 'objective']:
            result[entity_type] = list_entities(instance, entity_type)
        return result
    
    iter_entities = instance.__dict__.iteritems()
    
    if entity_type in ["set", "sets"]:
        return sorted((x, y.doc, get_onset_names(y)) for (x,y) in iter_entities 
                       if '.sets.' in str(type(y)) and not y.virtual)
         
    elif entity_type in ["par", "param", "params", "parameter", "parameters"]:
        return sorted((x, y.doc, get_onset_names(y)) for (x,y) in iter_entities 
                       if '.param.' in str(type(y)))
        
    elif entity_type in ["var", "vars", "variable", "variables"]:
        return sorted((x, y.doc, get_onset_names(y)) for (x,y) in iter_entities 
                       if '.var.' in str(type(y)))
        
    elif entity_type in ["con", "constraint", "constraints"]:
        return sorted((x, y.doc, get_onset_names(y)) for (x,y) in iter_entities 
                       if '.constraint.' in str(type(y)))
            
    elif entity_type in ["obj", "objective", "objectives"]:
        return sorted((x, y.doc, get_onset_names(y)) for (x,y) in iter_entities 
                       if '.objective.' in str(type(y)))
        
    else:
        return ValueError("Unknown parameter entity_type")

def get_entity_type(entity):
    type_str = str(type(entity))
    if '.sets.' in type_str:
        return 'set'
    elif '.param.' in type_str:
        return 'parameter'
    elif '.var.' in type_str:
        return 'variable'
    elif '.constraint.' in type_str:
        return 'constraint'
    elif '.objective.' in type_str:
        return 'objective'
    else:
        return 'unknown'


def get_onset_names(entity):
    # get column titles for entities from domain set names
    entity_type = get_entity_type(entity)

    labels = []
    
    if entity_type == 'set':
        if entity.dimen > 1 and entity.domain:
            # N-dimensional set tuples
            for domain_set in entity.domain.set_tuple:
                labels.append(domain_set.name)
        elif entity.domain:
            # 1D subset; simply add superset name
            labels.append(entity.domain.name)
        else:
            # no domain, so no labels needed
            pass
        
    elif entity_type == 'parameter':
        if entity.dim() > 0 and entity._index:
            labels = get_onset_names(entity._index)
        else:
            # zero dimensions, so no onset labels
            pass

    elif entity_type in ['variable', 'constraint', 'objective']:
        if entity._index_set:
            for domain_set in entity._index_set:
                if domain_set.dimen == 1:
                    labels.append(domain_set.name)
                else:
                    labels.extend(the_set.name for the_set in domain_set.domain.set_tuple)
        else:
            if entity._ndim > 0:
                if entity._index.dimen == 1:
                    labels.append(entity._index.name)
                else:
                    labels.extend(the_set.name for the_set in entity._index.domain.set_tuple)
            else:
                # 0-dimensional thing, so no labels needed
                pass
    else:
        raise ValueError("Function get_entity_type returne unknown entity type '"+entity_type+"'!")
        
    return labels

