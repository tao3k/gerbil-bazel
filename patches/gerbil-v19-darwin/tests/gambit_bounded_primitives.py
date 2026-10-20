"""Experimental bounded original-primitive entries; never a result cache."""
import re
from gambit_guarded_trace import macro, Refused


TARGETS = {
    'length': 1, '_23__23_length': 1,
    'reverse': 1, '_23__23_reverse': 1,
    '_23__23_structure_2d_instance_2d_of_3f_': 2,
    '_23__23_structure_2d_direct_2d_instance_2d_of_3f_': 2,
}


def pure_target(expression):
    if re.fullmatch(r'___(?:R[0-4]|SELF|PRM_\w+)', expression):
        return True
    try:
        name, args = macro(expression)
    except Refused:
        return False
    if name in {'STK', 'PRC', 'SUB'}:
        return len(args) == 1 and re.fullmatch(r'-?\d+', args[0]) is not None
    if name == 'CLO':
        return len(args) == 2 and pure_target(args[0]) and re.fullmatch(r'-?\d+', args[1]) is not None
    return False


def inject(modules):
    counts = []
    pattern = re.compile(
        r'(?m)^(GB_TRACE_INVALIDATE_AT\(\d+\);\n)?([ \t]*)(___JUMP(?:GLO(?:NOT)?SAFE|GEN(?:NOT)?SAFE|PRM)\(___SET_NARGS\(([12])\),([^\n]*)\))$')
    for module in modules:
        count = 0

        def replace(match):
            nonlocal count
            operation = match[3]
            _, parsed = macro(operation)
            args = parsed[1:]
            name = None
            if operation.startswith('___JUMPPRM'):
                if len(args) != 1 or not args[0].startswith('___PRM_'):
                    return match[0]
                name = args[0].removeprefix('___PRM_')
                expression = args[0]
            elif operation.startswith('___JUMPGEN'):
                if len(args) != 1 or not pure_target(args[0]):
                    return match[0]
                expression = args[0]
            else:
                if len(args) != 2 or not args[0].isdigit() or not args[1].startswith('___G_'):
                    return match[0]
                name = args[1].removeprefix('___G_')
                expression = f'___GLO({args[0]},{args[1]})'
            nargs = int(match[4])
            if name is not None and TARGETS.get(name) != nargs:
                return match[0]
            count += 1
            return f'{match[2]}GB_BOUNDED_PRIMITIVE_TRY({expression},{nargs})\n{match[1] or ""}{match[2]}{operation}'

        module['body'] = pattern.sub(replace, module['body'])
        counts.append({'module': module['path'].stem, 'sites': count})
    return {'boundedPrimitiveEntrySites': counts,
            'boundedPrimitivePolicy': 'original-primitive-live-reads-64-pairs-128-types-no-result-cache'}


PREAMBLE = r'''
#ifndef GB_BOUNDED_PRIMITIVE_HIT
#define GB_BOUNDED_PRIMITIVE_HIT(kind,size) ((void)0)
#endif
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES) && defined(___SINGLE_VM) && defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1) && (___NB_ARG_REGS == 3) && (___WS == 8) && (___PAIR_SIZE == 2) && (___PAIR_BODY == 1) && !defined(___USE_HANDLES) && !defined(___DEBUG_HEAP_LIMIT) && !defined(___DEBUG_STACK_LIMIT) && !defined(___HEARTBEAT_USING_POLL_COUNTDOWN)
___IMP_DATA(___glo_struct,___G_length);
___IMP_DATA(___glo_struct,___G__23__23_length);
___IMP_DATA(___glo_struct,___G_reverse);
___IMP_DATA(___glo_struct,___G__23__23_reverse);
___IMP_DATA(___glo_struct,___G__23__23_structure_2d_instance_2d_of_3f_);
___IMP_DATA(___glo_struct,___G__23__23_structure_2d_direct_2d_instance_2d_of_3f_);
static int __attribute__((noinline,optimize("O3")))
gb_bounded_list_size(___WORD input) {
  ___WORD ___temp;
  int size=0;
  while (___PAIRP(input)) {
    if (size>=64) return -1;
    input=___CDR(input);
    ++size;
  }
  return input==___NUL ? size : -1;
}
static int __attribute__((noinline,optimize("O3")))
gb_bounded_structure_test(___WORD input,___WORD id,int direct,___WORD *answer) {
  ___WORD ___temp;
  if (!___STRUCTUREP(input)) { *answer=___FAL; return 1; }
  if (___INT(___STRUCTURELENGTH(input))<1) return 0;
  ___WORD type=___STRUCTURETYPE(input);
  for (int depth=0; depth<128; ++depth) {
    if (!___STRUCTUREP(type) || ___INT(___STRUCTURELENGTH(type))<5) return 0;
    if (___EQP(___TYPEID(type),id)) { *answer=___TRU; return 1; }
    if (direct) { *answer=___FAL; return 1; }
    type=___TYPESUPER(type);
    if (type==___FAL) { *answer=___FAL; return 1; }
  }
  return 0;
}
#define GB_BOUNDED_PRIMITIVE_TRY(expression,nargs) do { \
  if (!___EXPECT_FALSE((___fp-32)<___ps->stack_trip)) { \
    ___WORD gb_primitive=(expression),gb_answer; \
    if ((nargs)==1) { \
      int gb_reverse=(gb_primitive==___PRMCELL(___G_reverse.prm) || \
                      gb_primitive==___PRMCELL(___G__23__23_reverse.prm)); \
      if (gb_reverse || gb_primitive==___PRMCELL(___G_length.prm) || \
                        gb_primitive==___PRMCELL(___G__23__23_length.prm)) { \
        int gb_size=gb_bounded_list_size(___R1); \
        if (gb_size>=0 && (!gb_reverse || ___hp+(3*gb_size)<=___ps->heap_limit)) { \
          if (gb_reverse) { \
            ___WORD gb_input=___R1; \
            gb_answer=___NUL; \
            for (int gb_i=0; gb_i<gb_size; ++gb_i) { \
              gb_answer=___CONS(___CAR(gb_input),gb_answer); \
              gb_input=___CDR(gb_input); \
            } \
          } else gb_answer=___FIX(gb_size); \
          ___SELF=gb_primitive; \
          ___SET_NARGS(1) \
          ___SET_R1(gb_answer) \
          GB_BOUNDED_PRIMITIVE_HIT(gb_reverse,gb_size); \
          ___JUMPRET(___R0) \
        } \
      } \
    } else if ((nargs)==2) { \
      int gb_direct=(gb_primitive==___PRMCELL(___G__23__23_structure_2d_direct_2d_instance_2d_of_3f_.prm)); \
      if ((gb_direct || gb_primitive==___PRMCELL(___G__23__23_structure_2d_instance_2d_of_3f_.prm)) && \
          gb_bounded_structure_test(___R1,___R2,gb_direct,&gb_answer)) { \
        ___SELF=gb_primitive; \
        ___SET_NARGS(2) \
        ___SET_R1(gb_answer) \
        GB_BOUNDED_PRIMITIVE_HIT(2,gb_direct); \
        ___JUMPRET(___R0) \
      } \
    } \
  } \
} while (0);
#else
#define GB_BOUNDED_PRIMITIVE_TRY(expression,nargs) ((void)0);
#endif
'''


def inject_runtime_unit(source, path):
    begin = '___BEGIN_M_COD\n'
    end = '___END_M_COD\n'
    if source.count(begin) != 1 or source.count(end) != 1:
        raise Refused('unique original runtime code region required')
    prefix, rest = source.split(begin)
    body, suffix = rest.split(end)
    modules = [{'path': path, 'body': body}]
    details = inject(modules)
    return prefix + PREAMBLE + begin + modules[0]['body'] + end + suffix, details
