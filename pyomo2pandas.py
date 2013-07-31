""" pyomo2pandas: read data from coopr.pyomo models to pandas DataFrames

Pyomo is a GAMS-like model description language for mathematical
optimization problems. It is part of a larger family of packages called
Coopr that provides interfaces to many solvers (e.g. CPLEX, XPRESS,
Gurobi, lpsolve, GLPK) for Pyomo models. This fact makes creating models
in this framework
"""
import pandas as pd
from datetime import datetime

def get_entity(instance, name):
    """ Return a DataFrame for an entity in model intance.
    """
    
    # retrieve
    entity = instance.__getattribute__(name)
    
    labels = get_onset_names(entity)

    # create DataFrame
    if entity._ndim > 1:
        # concatenate index tuples with value if entity has multidimensional indices v[0]
        results = pd.DataFrame([v[0]+(v[1].value,) for v in entity.iteritems()])
    else:
        # otherwise, create tuple from scalar index v[0]
        results = pd.DataFrame([(v[0], v[1].value) for v in entity.iteritems()])

    # check for duplicate labels
    if len(set(labels)) != len(labels):
        for k, label in enumerate(labels):
            if label in labels[:k]:
                labels[k] = labels[k] + "_"
        
    results.columns = labels + [name]
    results.set_index(labels, inplace=True)
    
    return results
    
def get_entities(instance, names):
    """ Return one DataFrame with entities in columns and a common index.
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

def list_entities(instance, entity_type):
    """ Return list of sets, params, variables, constraints or objectives
    
    Args:
        instance: a Pyomo ConcreteModel object
        type: "set", "param", "variable", "constraint" or "objective"
    """
    iter_entities = instance.__dict__.iteritems()
    
    if entity_type in ["set", "sets"]:
        return sorted((x, get_onset_names(y)) for (x,y) in iter_entities if '.sets.' in str(type(y)) and not y.virtual)
         
    elif entity_type in ["par", "param", "params", "parameter", "parameters"]:
        return sorted((x, get_onset_names(y)) for (x,y) in iter_entities if '.param.' in str(type(y)))
        
    elif entity_type in ["var", "vars", "variable", "variables"]:
        return sorted((x, get_onset_names(y)) for (x,y) in iter_entities if '.var.' in str(type(y)))
        
    elif entity_type in ["con", "constraint", "constraints"]:
        return sorted((x, get_onset_names(y)) for (x,y) in iter_entities if '.constraint.' in str(type(y)))
            
    elif entity_type in ["obj", "objective", "objectives"]:
        return sorted((x, get_onset_names(y)) for (x,y) in iter_entities if '.objective.' in str(type(y)))


def get_onset_names(entity):
    # get column titles for entities from domain set names
    labels = []
    if entity._index_set:
        for domain_set in entity._index_set:
            if domain_set.dimen == 1:
                labels.append(domain_set.name)
            else:
                labels.extend(the_set.name for the_set in domain_set.domain.set_tuple)
    else:
        if entity._index.dimen == 1:
            labels.append(entity._index.name)
        else:
            labels.extend(the_set.name for the_set in entity._index.domain.set_tuple)
    
    return labels

def now(mydateformat='%Y%m%dT%H%M%S'):
    return datetime.now().strftime(mydateformat)