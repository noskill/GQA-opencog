import re
import enum
from collections import defaultdict
import json

two_args_re = re.compile('^([\w\s]+)\((\d+)\)')
two_args_re_no = re.compile('^([\w\s]+)\((-)\)')
many_objects = re.compile('^(\w+)\s\((\d+(\,\d+)+)\)')
one_word = re.compile('^(\w+)($)')
s_re = re.compile('([s|o|_])\s\((.*)\)')

varnames = ['$X', '$Y', '$Z', '$E', '$R']

class RelType(enum.Enum):
    relation = 0
    complex = 1
    filter = 2


class RelDesc:
    def __init__(self, rel_type):
        self.type = rel_type

class NormalRelation(RelDesc):
    def __init__(self, rel_name):
        super().__init__(RelType.relation)
        self.rel_name = rel_name
    def build(self, *args, **kwargs):
        return Relation(self.rel_name, kwargs['rel_args'],
                        dependencies=kwargs['depend'], variables=kwargs['vars'])

class FilterRelation(RelDesc):
    def __init__(self, filter_type, filter_arg):
        super().__init__(RelType.filter)
        self.filter_type = filter_type
        self.filter_arg = filter_arg

    def build(self, *args, **kwargs):
        f = Filter(filter_type=self.filter_type,
                name=self.filter_arg, variables=kwargs['var_name'],
                dependencies=kwargs['depend'])
        return f

class ComplexRelation(RelDesc):
    def __init__(self, arg1, arg2):
        super().__init__(RelType.complex)
        self.rel1 = arg1
        self.rel2 = arg2

    def build(self, *args, **kwargs):
        res1 = self.rel1.build(**kwargs)
        kwargs['depend'] = [res1]
        # var_name = get_var_name(no_obj, '', vars)
        res2 = self.rel2.build(**kwargs)
        return res2

class OnTheEdge(ComplexRelation):

    def build(self, *args, **kwargs):
        var_name = get_var_name(kwargs['no_obj'], '', kwargs['variables'])
        kwargs1 = dict(**kwargs)
        assert len(kwargs1['rel_args']) == 2
        kwargs1['rel_args'] = var_name, kwargs['rel_args'][-1]
        res1 = self.rel1.build(**kwargs1)
        kwargs2 = dict(**kwargs)
        kwargs2['depend'] = [res1]
        kwargs2['rel_args'] = kwargs['rel_args'][0], var_name
        res2 = self.rel2.build(**kwargs2)
        return res2

class RelateSame(NormalRelation):
    def build(self, *args, **kwargs):
        no_obj = kwargs['no_obj']
        variables = kwargs['variables']
        color1_var_name = get_var_name(no_obj, '', variables)
        color2_var_name = get_var_name(no_obj, '', variables)
        select_color1 = Filter('color', color1_var_name, [kwargs['rel_args'][0]],
                               dependencies=kwargs['depend'])
        select_color2 = Filter('color', color2_var_name, [kwargs['rel_args'][1]],
                               dependencies=kwargs['depend'])
        result = Equals([color1_var_name, color2_var_name], kwargs['vars'],
                        dependencies=[select_color1, select_color2])
        return result



relations = {
    'to the right of': 'right_of',
    'on': 'on',
    'to the left of': 'left_of',
    'by': 'by',
    'in': 'in',
    'carrying': 'carrying',
    'behind': 'behind',
    'wearing': 'wearing',
    'near': 'near',
    'along': 'along',
    'in front of': 'front_of',
    'hitting': 'hitting',
    'with': 'with',
    'full of': 'full_of',
    'on top of': 'on_top_of',
    'above': 'above',
    'covered in': 'covered_in',
    'of': 'of',
    'feeding': 'feeding',
    'holding': 'holding',
    'drinking from': 'drinks_from',
    'riding': 'rides',
    'using': 'uses',
    'below': 'below',
    'hanging on': 'hangs_on',
    'hanging from': 'hangs_on',
    'leaning against': 'leans_against',
    'kicking': 'kicks',
    'next to': 'next_to',
    'eating': 'eating',
    'surrounding': 'surrounds',
    'pulled by': 'pulled_by',
    'looking at': 'looking_at',
    'looking': 'looking_at',
    'under': 'under',
    'throwing': 'throwing',
    'topped with': 'topped_with',
    'around': 'around',
    'covering': 'covering',
    'pulling': 'pulling',
    'leading': 'leading',
    'riding on': 'rides',
    'beside': 'beside',
    'playing with': 'playing_with',
    'hugging': 'hugging',
    'edge of': 'edge_of',
    'facing': 'facing',
    'watching': 'watching',
    'inside': 'in',
    'opening': 'opening',
    'close to': 'close',
    'talking on': 'talking_on',
    'leaning on': 'leaning_on',
    'beneath': 'below',
    'jumping over': 'jumping_over',
    'between': 'between',
    'filled with': 'filled_with',
    'touching': 'touching',
    'at': 'at',
    'cutting': 'cutting',
    'smoking': 'smoking',
    'following': 'following',
    'covered with': 'covered_in',
    'printed on': 'printed_on',
}

relations = {k: NormalRelation(v) for (k,v) in relations.items()}
complex_relations = {
    'standing in front of': (FilterRelation('pose', 'standing'),
                            relations['in front of']),
    'sitting on top of': (FilterRelation('pose', 'sitting'),
                            relations['on top of']),
    'standing on': (FilterRelation('pose', 'standing'),
                    relations['on']),
    'sitting on': (FilterRelation('pose', 'sitting'),
                    relations['on']),
    'sitting at': (FilterRelation('pose', 'sitting'),
                    relations['at']),
    'sitting in': (FilterRelation('pose', 'sitting'),
                    relations['in']),
    'walking on': (FilterRelation('pose','walking'),
                    relations['on']),
    'walking past': (FilterRelation('pose','walking'),
                    relations['near']),
    'walking along': (FilterRelation('pose','walking'),
                    relations['along']),
    'lying in': (FilterRelation('pose','lays'),
                   relations['in']),
    'lying on': (FilterRelation('pose','lays'),
                    relations['on']),
    'hanging above': (FilterRelation('pose', 'hanging'),
                      relations['above']),
    'sitting near': (FilterRelation('pose', 'sitting'),
                     relations['near']),
    'standing by': (FilterRelation('pose', 'standing'),
                     relations['near']),
    'parked in': (FilterRelation('pose', 'parked'),
                  relations['in']),
    'parked on': (FilterRelation('pose', 'parked'),
                  relations['on']),
}

complex_relations = {k: ComplexRelation(*v) for (k, v) in complex_relations.items()}
relations.update(complex_relations)
relations.update({'on the edge of': OnTheEdge(relations['edge of'],
                       relations['on'])})
relations.update({'same color': RelateSame('same_color')})

def make_filter(name, var):
    return name + '(' + var + ')'


def build_conjuntion(result, dep):
    result.append(dep)
    for d in dep.dependencies:
        build_conjuntion(result, d)


class Node:
    def __init__(self, dependencies, variables):
        self.dependencies = dependencies
        self.variables = variables

    def __str__(self):
        return 'Node'

    def build_expression(self):
        conj = []
        for d in self.dependencies:
            tmp = []
            build_conjuntion(tmp, d)
            conj.extend(tmp)
        return str(self) + ',' + ','.join([str(x) for x in conj])


class Filter(Node):
    def __init__(self, filter_type, name, variables, dependencies=None):
        super().__init__(dependencies, variables)
        self.name = name
        self.filter_type = filter_type

    def __str__(self):
        return self.filter_type + '({0}, {1})'.format(self.name, self.variables[0])


class Exists(Node):
    def __init__(self, variables, dependencies=None):
        super().__init__(dependencies, variables)
        assert len(dependencies) == 1

    def __str__(self):
        return 'exists({0})'.format(self.variables[0])


class Disjunction(Node):

    def __str__(self):
        return 'Or(' + ','.join(str(d) for d in self.dependencies) + ')'

    def build_expression(self):
        conjunts = []
        for dep in self.dependencies:
            tmp = []
            build_conjuntion(tmp, dep)
            conjunts.append(tmp)
        str_conj = [','.join(str(c) for c  in conj) for conj in conjunts]
        assert(len(str_conj) == 2)
        return '({0});({1})'.format(*str_conj)


class Conjunction(Node):
    def __str__(self):
        return ','.join(str(d) for d in self.dependencies)

    def build_expression(self):
        conj = []
        for d in self.dependencies:
            tmp = []
            build_conjuntion(tmp, d)
            conj.extend(tmp)
        return ','.join([str(x) for x in conj])


class Relation(Node):
    def __init__(self, rel_name, args, dependencies, variables):
        super().__init__(dependencies, variables=variables)
        self.relation = rel_name
        self.args = args

    def __str__(self):
        return self.relation + '({0}, {1})'.format(*[str(d) for d in self.args])


class Verify(Node):
    def __init__(self, verify_type, verify_arg, dependencies, variables):
        super().__init__(dependencies=dependencies, variables=variables)
        self.verify_type = verify_type
        self.verify_arg = verify_arg
        assert len(dependencies) == 1

    def __str__(self):
        return 'verify_{0}({1}, {2})'.format(self.verify_type, self.verify_arg, self.variables[0])

    def build_expression(self):
        tmp = []
        build_conjuntion(tmp, self.dependencies[0])
        return str(self) + ',' + ','.join([str(x) for x in tmp])


class Query(Node):
    def __init__(self, arg, dependencies, variables):
        super().__init__(dependencies=dependencies, variables=variables)
        self.arg = arg
        assert len(dependencies) == 1

    def __str__(self):
        return 'query({0}, {1})'.format(self.arg, self.variables[0])


class Difference(Node):
    _name = 'different'

    def __init__(self, arg, dependencies, variables):
        super().__init__(dependencies=dependencies, variables=variables)
        self.arg = arg

    def __str__(self):
        if len(self.variables) == 2:
            return self._name + '({0}, {1}, {2})'.format(self.arg, *self.variables)
        else:
            assert len(self.variables) == 1
            return self._name + '({0}, {1})'.format(self.arg, self.variables[0])


class Equals(Node):
    def __init__(self, args, variables, dependencies=None):
        super().__init__(dependencies, variables)
        assert len(args) == 2
        assert len(variables) == 2
        assert len(dependencies) == 2
        self.args = args

    def __str__(self):
        return 'equals({0}, {1})'.format(*self.args)

class IfElse(Node):
    def __init__(self, comparator, dependencies):
        var = [dependencies[0].variables[0]]
        var.append(dependencies[1].variables[0])
        super().__init__(dependencies, var)
        self.comparator = comparator

    def __str__(self):
        comp = '{0}({1}, {2})'.format(self.comparator, *self.variables)
        out = self.dependencies[0].name, self.dependencies[1].name
        return 'cond({0}, {1}, {2})'.format(comp, *out)



class Same(Difference):
    _name = 'same'


class Common(Node):
    def __init__(self, dependencies, variables):
        super().__init__(dependencies=dependencies, variables=variables)
        assert len(variables) == 2

    def __str__(self):
        return 'query_common({0}, {1})'.format(*self.variables)


def build_relate(argument, dependencies, deps, variables, no_obj):
    args = argument.split(',')
    assert len(args) == 3
    rel_type, obj_id = s_re.match(args[2]).groups()
    var_name = get_var_name(no_obj, obj_id, variables)
    assert len(dependencies) == 1
    vars = deps[0].variables
    #assert(len(vars) == 1)
    if args[0] != '_':
        f = Filter(filter_type='object', name=args[0], variables=[var_name], dependencies=deps)
        depend = [f]

    else:
        depend = deps

    if rel_type == 's':
        vars = [var_name, vars[0]]
        rel_args = [vars[0], vars[1]]
    else:
        vars = [var_name, vars[0]]
        rel_args = [vars[1], vars[0]]
    relation = args[1]
    rel_mapped = relations[relation]
    return rel_mapped.build(rel_args=rel_args,
            depend=depend, var_name=var_name, vars=vars,
            no_obj=no_obj, variables=variables)

def convert(items, ops, variables, no_obj):
    if not items:
        return ops[-1].build_expression()
    item = items[0]
    items = items[1:]
    operation = item['operation'].strip().split()
    dependencies = item['dependencies']
    deps = [ops[i] for i in dependencies]
    argument = item['argument']
    if operation[0] == 'select':
        if argument:
            for reg in [two_args_re, two_args_re_no, one_word]:
                m = reg.match(argument)
                if m:
                    name, obj_id = m.groups()
                    var_name = get_var_name(no_obj, obj_id, variables)
                    ops.append(Filter('object', name.strip(), [var_name], deps))
                    break
            if m is None:
                m = many_objects.match(argument)
                name , obj_ids = m.groups()[:2]
                # match objects to a list!
                var_name = get_var_name(no_obj, obj_ids, variables)
                ops.append(Filter('object', name.strip(), ['[{0}]'.format(var_name)], deps))
        else:
            import pdb;pdb.set_trace()
    elif operation[0] == 'filter':
        if len(operation) == 1:
            operation.append('is')
        if len(operation) == 3:
            operation = [operation[0], '_'.join(operation[1:])]
        assert len(operation) == 2
        assert len(dependencies) == 1
        vars = deps[0].variables
        ops.append(Filter(filter_type=operation[1], name=argument, variables=vars, dependencies=deps))
    elif operation[0] == 'exist':
        assert len(dependencies) == 1
        vars = deps[0].variables
        ops.append(Exists(dependencies=deps, variables=vars))
    elif operation[0] == 'or':
        vars = extract_deps(deps)
        ops.append(Disjunction(dependencies=deps, variables=vars))
    elif operation[0] == 'relate':
         ops.append(build_relate(argument, dependencies, deps, variables, no_obj))
    elif operation[0] == 'verify':
        if len(operation) == 1:
            operation.append('is')
        if operation[1] == 'rel':
            ops.append(build_relate(argument, dependencies, deps, variables, no_obj))
        else:

            ops.append(Verify(verify_type=operation[1], verify_arg=argument,
                          variables=deps[0].variables, dependencies=deps))
    elif operation[0] == 'and':
        vars = extract_deps(deps)
        ops.append(Conjunction(dependencies=deps, variables=vars))
    elif operation[0] == 'query':
        ops.append(Query(argument, deps, deps[0].variables))
    elif operation[0] == 'choose':
        tmp = []
        if len(operation) == 2 and operation[1] in ('younger', 'older'):
            assert len(deps) == 2
            import pdb;pdb.set_trace()
            op1 = IfElse(operation[1], deps)
            ops.append(op1)
        else:
            if len(operation) == 1:
                operation.append('is')
            assert len(deps) == 1
            if operation[1] == 'rel':
                left, middle, right = argument.split(',')
                template = '{0},{1},{2}'
                for rel_arg in middle.split('|'):
                    new_argument = template.format(left, rel_arg, right)
                    op1 = build_relate(new_argument, dependencies, deps, variables, no_obj)
                    tmp.append(op1)
            else:
                for arg in argument.split('|'):
                    op1 = Verify(verify_type=operation[1], verify_arg=arg,
                                          variables=deps[0].variables, dependencies=deps)
                    tmp.append(op1)
            vars = extract_deps(deps)
            ops.append(Disjunction(dependencies=tmp, variables=vars))
    elif operation[0] == 'different':
        vars = same_difference_params(argument, deps, operation)
        ops.append(Difference(operation[1], dependencies=deps, variables=vars))
    elif operation[0] == 'same':
        vars = same_difference_params(argument, deps, operation)
        ops.append(Same(operation[1], dependencies=deps, variables=vars))
    elif operation[0] == 'common':
        vars = deps[0].variables[0], deps[1].variables[0]
        ops.append(Common(dependencies=deps, variables=vars))
    else:
        import pdb;pdb.set_trace()
    return convert(items, ops, variables, no_obj)


def same_difference_params(argument, deps, operation):
    if len(deps) == 2:
        vars = deps[0].variables[0], deps[1].variables[0]
        assert all(not x.startswith('[') for x in vars)
    if len(deps) == 1:
        vars = [deps[0].variables[0]]
        assert len(deps[0].variables) == 1
    if len(operation) == 1:
        operation.append(argument)
    return vars


def extract_deps(deps):
    vars = []
    for d in deps:
        for var in d.variables:
            if var not in vars:
                vars.append(var)
    return vars


def get_var_name(no_obj, obj_id, variables):
    if (not obj_id) or (obj_id == '-'):
        obj_id = obj_id + str(no_obj[0])
        no_obj[0] += 1
    if obj_id not in variables:
        variables[obj_id] = varnames[len(variables)]
    var_name = variables[obj_id]
    return var_name


def main():
    import sys
    if len(sys.argv) != 2:
        print('give path to TRAIN json file as an argument')
    path = sys.argv[1]
    data = json.load(open(path))

    for i, key in enumerate(data.keys()):
        sem = data[key]['semantic']
        variables = dict()
        no_obj_count = [0]
        items = []
        # print(i)
        # print(json.dumps(data[key]['semantic'], indent=2))
        print('{0}: '.format(i), data[key]['question'])
        res = convert(sem, items, variables, no_obj_count)
        print('{0}: '.format(i), res)
        if i > 20000:
            break




main()
