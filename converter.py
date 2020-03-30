import re
import copy
import enum
from collections import defaultdict
import json

two_args_re = re.compile('^((\w+(?:-\w+)?\s?)+)\((\d+)\)')
two_args_re = re.compile('^((\w+(?:-\w+)?\s?)+)\((\d+)\)')
two_args_re_no = re.compile('^((\w+(?:-\w+)?\s?)+)\((-)\)')
many_objects = re.compile('^(\w+)\s\((\d+(\,\d+)+)\)')
one_word = re.compile('^((\w+(?:-\w+)?\s?)+)($)')
s_re = re.compile('([s|o|_])\s\((.*)\)')

varnames = ['$X', '$Y', '$Z', '$E', '$R']

class RelType(enum.Enum):
    relation = 0
    complex = 1
    filter = 2


class RelDesc:
    def __init__(self, rel_type):
        self.type = rel_type

    @staticmethod
    def get_rel_args(**kwargs):
        vars = kwargs['vars']
        rel_type = kwargs['rel_type']
        var_name = kwargs['var_name']
        if rel_type == 's':
            vars = [var_name, vars[0]]
            rel_args = [vars[0], vars[1]]
        else:
            vars = [var_name, vars[0]]
            rel_args = [vars[1], vars[0]]
        return rel_args, vars



class NormalRelation(RelDesc):
    def __init__(self, rel_name):
        super().__init__(RelType.relation)
        self.rel_name = rel_name

    def build(self, *args, **kwargs):
        args, vars = self.get_rel_args(**kwargs)
        return Relation(self.rel_name, args=args,
                        dependencies=kwargs['depend'], variables=vars)


class WornOn(NormalRelation):
    def build(self, *args, **kwargs):
        args, vars = self.get_rel_args(**kwargs)
        return Relation(self.rel_name, list(reversed(args)),
                        dependencies=kwargs['depend'], variables=vars)


class RelateSame(NormalRelation):
    def build(self, *args, **kwargs):
        rel_args, vars = self.get_rel_args(**kwargs)
        no_obj = kwargs['no_obj']
        variables = kwargs['variables']
        rel = self.rel_name
        color1_var_name = get_var_name(no_obj, '', variables)
        color2_var_name = get_var_name(no_obj, '', variables)
        select_color1 = Filter(rel, color1_var_name, [rel_args[0]],
                               dependencies=kwargs['depend'])
        select_color2 = Filter(rel, color2_var_name, [rel_args[1]],
                               dependencies=kwargs['depend'])
        kwargs['vars'] = [color1_var_name, color2_var_name]
        result = Equals([color1_var_name, color2_var_name], vars,
                        dependencies=[select_color1, select_color2])
        return result


class FilterRelation(RelDesc):
    def __init__(self, filter_type, filter_arg):
        super().__init__(RelType.filter)
        self.filter_type = filter_type
        self.filter_arg = filter_arg

    def build(self, *args, **kwargs):
        assert isinstance(kwargs['var_name'], str)
        rel_args, vars = self.get_rel_args(**kwargs)
        f = Filter(filter_type=self.filter_type,
                name=self.filter_arg, variables=[rel_args[0]],
                dependencies=kwargs['depend'])
        return f


class ComplexRelation(RelDesc):
    def __init__(self, arg1, arg2):
        super().__init__(RelType.complex)
        self.rel1 = arg1
        self.rel2 = arg2

    def build(self, *args, **kwargs):
        rel_type = kwargs['rel_type']
        res1 = self.rel1.build(**kwargs)
        kwargs['depend'] = [res1]
        res2 = self.rel2.build(**kwargs)
        return res2


class OnTheEdge(ComplexRelation):
    _position = 'on'
    def build(self, *args, **kwargs):
        var_name = get_var_name(kwargs['no_obj'], '', kwargs['variables'])
        kwargs1 = copy.copy(kwargs)
        kwargs1['var_name'] = kwargs['vars'][0]
        kwargs1['rel_type'] = 'o'
        kwargs1['vars'] = [var_name]
        res1 = self.rel1.build(**kwargs1)
        kwargs2 = copy.copy(kwargs)
        kwargs2['depend'] = [res1]
        kwargs2['var_name'] = var_name
        kwargs2['vars'] = [kwargs['var_name']]
        kwargs2['rel_type'] = 'o'
        res2 = Relation(self._position, args=[kwargs['var_name'], var_name], dependencies=[res1], variables=[kwargs['var_name']])
        return res2

class InTheCenter(OnTheEdge):
    _position = 'in'

    def build(self, *args, **kwargs):
        var_name = get_var_name(kwargs['no_obj'], '', kwargs['variables'])
        kwargs1 = copy.copy(kwargs)
        kwargs1['var_name'] = kwargs['vars'][0]
        kwargs1['rel_type'] = 'o'
        kwargs1['vars'] = [var_name]
        if kwargs['rel_type'] == 'o':
            kwargs1['var_name'] = kwargs['var_name']
        res1 = self.rel1.build(**kwargs1)
        if kwargs['rel_type'] == 'o':
            res2 = Relation(self._position, args=[kwargs['vars'][0], var_name], dependencies=[res1], variables=[kwargs['var_name']])
        else:
            res2 = Relation(self._position, args=[kwargs['var_name'], var_name], dependencies=[res1], variables=[kwargs['var_name']])
        return res2


relations = {
    'to the right of': 'right_of',
    'in the middle of': 'in_middle_of',
    'on': 'on',
    'to the left of': 'left_of',
    'by': 'by',
    'in': 'in',
    'underneath': 'under',
    'carrying': 'carrying',
    'behind': 'behind',
    'observing': 'observing',
    'perched on': 'on',
    'wearing': 'wearing',
    'near': 'near',
    'along': 'along',
    'in front of': 'front_of',
    'on the back of': 'back_of',
    'hitting': 'hitting',
    'with': 'with',
    'full of': 'full_of',
    'on top of': 'on_top_of',
    'above': 'above',
    'covered in': 'covered_in',
    'covered by': 'covered_in',
    'wrapped in': 'wrapped_in',
    'of': 'of',
    'helping': 'helping',
    'feeding': 'feeding',
    'reflected in': 'reflected_in',
    'holding': 'holding',
    'holding onto': 'holding',
    'drinking from': 'drinks_from',
    'riding': 'rides',
    'using': 'uses',
    'below': 'below',
    'hanging on': 'hangs_on',
    'hung on': 'hangs_on',
    'hanging from': 'hangs_on',
    'leaning against': 'leans_against',
    'kicking': 'kicks',
    'plugged into': 'plugged_into',
    'next to': 'next_to',
    'smiling at': 'smiling_at',
    'eating': 'eating',
    'drinking': 'drinking',
    'flying': 'flying',
    'draped over': 'draped_over',
    'surrounding': 'surrounding',
    'pulled by': 'pulled_by',
    'looking at': 'looking_at',
    'looking down at': 'looking_at',
    'looking into': 'looking_into',
    'looking': 'looking_at',
    'under': 'under',
    'over': 'over',
    'preparing': 'preparing',
    'throwing': 'throwing',
    'topped with': 'topped_with',
    'around': 'around',
    'covering': 'covering',
    'pulling': 'pulling',
    'leading': 'leading',
    'riding on': 'riding',
    'riding in': 'riding',
    'beside': 'beside',
    'playing with': 'playing_with',
    'hugging': 'hugging',
    'edge of': 'edge_of',
    'center of': 'center_of',
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
    'slicing': 'slicing',
    'picking up': 'picking up',
    'filled with': 'filled_with',
    'touching': 'touching',
    'at': 'at',
    'cutting': 'cutting',
    'smoking': 'smoking',
    'following': 'following',
    'covered with': 'covered_in',
    'printed on': 'printed_on',
    'pushed by': 'pushed_by',
    'posing with': 'posing with',
    'hanging off': 'hanging_off',
    'cleaning': 'cleaning',
    'attached to': 'attached_to',
    'looking through': 'looking_through',
    'looking in': 'looking_in',
    'stuck in': 'stuck_in',
    'grazing on': 'grazing',
    'leaning over': 'leaning_over',
    'on the side of': 'on_side',
    'on the front of': 'on_front',
    'swinging': 'swinging',
    'reaching for': 'reaching_for',
    'growing on': 'growing_on',
    'biting': 'biting',
    'leaving': 'leaving',
    'entering': 'entering',
    'contain': 'contain',
    'crossing': 'crossing',
    'licking': 'licking',
    'connected to': 'connected_to',
    'catching': 'catching',
    'kept in': 'kept_in',
    'playing': 'playing',
    'making': 'making',
    'photographing': 'photographing',
    'guiding': 'guiding',
    'reading': 'reading',
    'driving': 'driving',
    'pushing': 'pushing',
    'petting': 'petting',
    'waiting for': 'waiting_for',
    'selling': 'selling',
    'sniffing': 'sniffing',
    'coming from': 'coming_from',
    'coming out of': 'comming_from',
    'typing on': 'typing_on',
    'brushing': 'brushing',
    'mounted on': 'on',
    'seen through': 'seen_through',
    'beyond': 'behind',
    'across': 'across',
    'walking across': 'walking_across',
    'moving': 'moving',
    'working on': 'working_on',
}

relations = {k: NormalRelation(v) for (k,v) in relations.items()}
complex_relations = {
    'parked next to': (FilterRelation('activity', 'parked'),
                            relations['next to']),
    'standing next to': (FilterRelation('activity', 'standing'),
                            relations['next to']),
    'standing in front of': (FilterRelation('activity', 'standing'),
                            relations['in front of']),
    'sitting on top of': (FilterRelation('activity', 'sitting'),
                            relations['on top of']),
    'running in': (FilterRelation('activity', 'running'),
                    relations['in']),
    'walking down': (FilterRelation('activity', 'walking'),
                    relations['on']),
    'driving down': (FilterRelation('activity', 'driving'),
                    relations['on']),
    'driving on': (FilterRelation('activity', 'driving'),
                    relations['on']),
    'standing on': (FilterRelation('activity', 'standing'),
                    relations['on']),
    'sitting with': (FilterRelation('activity', 'sitting'),
                    relations['with']),
    'sitting next to': (FilterRelation('activity', 'sitting'),
                    relations['next to']),
    'skiing on': (FilterRelation('activity', 'skiing'),
                    relations['on']),
    'sitting on': (FilterRelation('activity', 'sitting'),
                    relations['on']),
    'standing behind': (FilterRelation('activity', 'standing'),
                    relations['behind']),
    'sitting behind': (FilterRelation('activity', 'sitting'),
                    relations['behind']),
    'sitting at': (FilterRelation('activity', 'sitting'),
                    relations['at']),
    'sitting in': (FilterRelation('activity', 'sitting'),
                    relations['in']),
    'sitting in front of': (FilterRelation('activity', 'sitting'),
                    relations['in front of']),
    'walking in': (FilterRelation('activity','walking'),
                    relations['in']),
    'resting on': (FilterRelation('activity','resting'),
                    relations['on']),
    'walking on': (FilterRelation('activity','walking'),
                    relations['on']),
    'traveling on': (FilterRelation('activity','treveling'),
                    relations['on']),
    'walking past': (FilterRelation('activity','walking'),
                    relations['near']),
    'walking along': (FilterRelation('activity','walking'),
                    relations['along']),
    'flying in': (FilterRelation('activity', 'flying'),
                    relations['in']),
    'stacked on': (FilterRelation('activity', 'stacked'),
                    relations['on']),
    'floating on': (FilterRelation('activity', 'floating'),
                    relations['on']),
    'floating in': (FilterRelation('activity', 'floating'),
                    relations['in']),
    'lying in': (FilterRelation('activity','lays'),
                   relations['in']),
    'skating on': (FilterRelation('activity','skating'),
                    relations['on']),
    'playing in': (FilterRelation('activity','playing'),
                    relations['in']),
    'playing on': (FilterRelation('activity','playing'),
                    relations['on']),
    'lying on': (FilterRelation('activity','lays'),
                    relations['on']),
    'lying next to': (FilterRelation('activity','lays'),
                        relations['next to']),
    'lying on top of': (FilterRelation('activity','lays'),
                        relations['on']),
    'standing on top of': (FilterRelation('activity','standing'),
                           relations['on']),
    'hanging above': (FilterRelation('activity', 'hanging'),
                      relations['above']),
    'standing near': (FilterRelation('activity', 'standing'),
                     relations['near']),
    'sitting near': (FilterRelation('activity', 'sitting'),
                     relations['near']),
    'standing by': (FilterRelation('activity', 'standing'),
                     relations['near']),
    'standing in': (FilterRelation('activity', 'standing'),
                     relations['in']),
    'parked in': (FilterRelation('activity', 'parked'),
                  relations['in']),
    'parked at': (FilterRelation('activity', 'parked'),
                  relations['at']),
    'eating in': (FilterRelation('activity', 'eating'),
                  relations['in']),
    'parked on': (FilterRelation('activity', 'parked'),
                  relations['on']),
    'sitting beside': (FilterRelation('activity', 'sitting'),
                       relations['beside']),
    'standing beside': (FilterRelation('activity', 'standing'),
                       relations['beside']),
    'standing at': (FilterRelation('activity', 'standing'),
                       relations['at']),
    'standing under': (FilterRelation('activity', 'standing'),
                       relations['under']),
    'walking with': (FilterRelation('activity', 'walking'),
                     relations['with']),
}

complex_relations = {k: ComplexRelation(*v) for (k, v) in complex_relations.items()}
relations.update(complex_relations)
relations.update({'on the edge of': OnTheEdge(relations['edge of'],
                       relations['on'])})
relations.update({'in the center of': InTheCenter(relations['center of'],
                       relations['in'])})
relations.update({'same color': RelateSame('color')})
relations.update({'same material': RelateSame('material')})
relations.update({'worn on': WornOn('wearing')})
relations.update({'surrounded by': WornOn('surrounding')})
relations.update({'wrapped around': WornOn('wrapped_in')})

def make_filter(name, var):
    return name + '(' + var + ')'


def build_conjuntion(result, dep):
    if dep not in result:
        result.append(dep)
    for d in dep.dependencies:
        build_conjuntion(result, d)


class Node:
    def __init__(self, dependencies, variables):
        assert isinstance(variables, (tuple, list))
        assert isinstance(dependencies, (tuple, list))
        self.dependencies = dependencies
        self.variables = variables
        self.__hash = None

    def __str__(self):
        return 'Node'

    def build_expression(self):
        conj = []
        for d in self.dependencies:
            tmp = []
            build_conjuntion(tmp, d)
            conj.extend(tmp)
        return str(self) + ' and ' + ' and '.join([str(x) for x in conj])

    def __hash__(self):
        if self.__hash is None:
            self.__hash = hash(str(self))
        return self.__hash


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
        str_conj = [' and '.join(str(c) for c  in conj) for conj in conjunts]
        assert(len(str_conj) == 2)
        return '{0} or {1}'.format(*str_conj)


class Conjunction(Node):
    def __str__(self):
        return ' and '.join(str(d) for d in self.dependencies)

    def build_expression(self):
        tmp = []
        for x in self.build():
            x_str = str(x)
            if x_str not in tmp:
                tmp.append(x_str)
        return ' and '.join(tmp)

    def build(self):
        conj = []
        for d in self.dependencies:
            tmp = []
            build_conjuntion(tmp, d)
            conj.extend(tmp)
        return conj



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
        return str(self) + ' and ' + ' and '.join([str(x) for x in tmp])


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


class IfElseNot(IfElse):
    def __str__(self):
        comp = '{0}({1}, {2})'.format(self.comparator, *self.variables)
        out = self.dependencies[0].name, self.dependencies[1].name
        return 'cond({0}, {2}, {1})'.format(comp, *out)


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
    relation = args[1]
    rel_mapped = relations[relation]
    return rel_mapped.build(rel_type=rel_type,
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
                    name, obj_id = m.group(1), m.group(3)
                    name = name.strip()
                    name = name.replace(' ', '_')
                    var_name = get_var_name(no_obj, obj_id, variables)
                    ops.append(Filter('object', name.strip(), [var_name], deps))
                    break
            if m is None:
                m = many_objects.match(argument)
                name, obj_id = m.groups()[:2]
                name = name.strip()
                name = name.replace(' ', '_')
                # match objects to a list!
                var_name = get_var_name(no_obj, obj_id, variables)
                ops.append(Filter('object', name.strip(), ['list({0})'.format(var_name)], deps))
            assert ' ' not in obj_id
            assert ' ' not in name
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
        if len(operation) == 2 and operation[1] in ('younger', 'older',
                'healthier'):
            assert len(deps) == 2
            op1 = IfElse(operation[1], deps)
            ops.append(op1)
        elif len(operation) == 3 and operation[2] in ('healthy'):
            assert operation[1] == 'less'
            op1 = IfElseNot('healthier', deps)
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
        #if i == 6031: # file 3 or 4
        sem = data[key]['semantic']
        variables = dict()
        no_obj_count = [0]
        items = []
        # print(i)
        # print(json.dumps(data[key]['semantic'], indent=2))
        print('{0}: '.format(i), data[key]['question'])
        res = convert(sem, items, variables, no_obj_count)
        print('{0}: '.format(i), res)

main()
