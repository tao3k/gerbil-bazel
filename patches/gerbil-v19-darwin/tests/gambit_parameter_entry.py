"""Prototype caller-side parameter reads; no parameter-value cache."""
import re


def share_result_storage(content):
    """Private candidate: one activation-local result consumed before each jump."""
    declaration = 'struct gb_parameter_result { ___WORD value,getter; int slot; };'
    local = '    struct gb_parameter_result gb_answer; \\\n'
    host = '#define ___MH_PROC gb_coalesced_host\n'
    if any(content.count(anchor) != 1 for anchor in (declaration, local, host)):
        raise ValueError('exact guarded parameter macro and common host required')
    begin = content.index('___BEGIN_M_COD\n', content.index(host))
    end = content.index('___END_M_COD', begin)
    calls = [m.start() for m in re.finditer(r'^[ \t]*GB_PARAMETER_TRY\(', content, re.MULTILINE)]
    if not calls or any(not begin < position < end for position in calls):
        raise ValueError('parameter fast paths must belong to the common host')
    content = content[:begin] + content[begin:].replace('___BEGIN_M_COD\n',
        '___BEGIN_M_COD\n#ifdef GB_SHARED_PARAMETER_RESULT\n'
        'struct gb_parameter_result gb_answer;\n#endif\n', 1)
    content = content.replace(local, '')
    content = content.replace(declaration, declaration + '\n#define GB_SHARED_PARAMETER_RESULT 1')
    return content


def inject(modules):
    counts = []
    pattern = re.compile(r"___JUMPGLO(NOT)?SAFE\(___SET_NARGS\(0\),(\d+),(___G_\w+)\)")
    for module in modules:
        count = 0
        def replace(match):
            nonlocal count
            count += 1
            return ("GB_PARAMETER_TRY(___GLO(" + match[2] + "," + match[3] + "))\n"
                    + match[0])
        module["body"] = pattern.sub(replace, module["body"])
        counts.append({"module": module["path"].stem, "sites": count})
    return {"parameterEntrySites": counts, "parameterEntryPolicy": "original-primitive-closure-live-three-slot-cache-and-getter"}


PREAMBLE = r"""
#ifndef GB_PARAMETER_HIT
#define GB_PARAMETER_HIT() ((void)0)
#endif
#ifndef GB_PARAMETER_SLOT
#define GB_PARAMETER_SLOT(slot) ((void)0)
#endif
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES) && defined(___SINGLE_VM) && defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1) && (___NB_ARG_REGS == 3) && !defined(___DYNAMIC) && !defined(___HEARTBEAT_USING_POLL_COUNTDOWN) && !defined(___DEBUG_STACK_LIMIT)
___IMP_DATA(___glo_struct,___G__23__23_make_2d_parameter);
___IMP_DATA(___glo_struct,___G__23__23_dynamic_2d_ref);
___IMP_DATA(___glo_struct,___G__23__23_current_2d_exception_2d_handler);
___IMP_DATA(___glo_struct,___G__23__23_current_2d_input_2d_port);
___IMP_DATA(___glo_struct,___G__23__23_current_2d_output_2d_port);
struct gb_parameter_result { ___WORD value,getter; int slot; };
static int __attribute__((noinline,optimize("O3")))
gb_parameter_lookup(___processor_state ___ps,___WORD gb_param,struct gb_parameter_result *result) {
  ___WORD ___temp;
  if (!___CLOSUREP(gb_param) ||
      ___LABEL_ENTRY_GET(gb_param)!=___PRMCELL(___G__23__23_make_2d_parameter.prm)+(5*___LABEL_SIZE*___WS) ||
      ___CLO(gb_param,2)!=gb_param ||
      ___GLOCELL(___G__23__23_dynamic_2d_ref.val)!=___PRMCELL(___G__23__23_dynamic_2d_ref.prm) ||
      gb_param==___GLOCELL(___G__23__23_current_2d_exception_2d_handler.val) ||
      gb_param==___GLOCELL(___G__23__23_current_2d_input_2d_port.val) ||
      gb_param==___GLOCELL(___G__23__23_current_2d_output_2d_port.val)) return 0;
  ___WORD gb_thread=___CURRENTTHREAD;
  ___WORD gb_cache=___THREAD_DENV_CACHE1_FIELD(gb_thread);
  int gb_slot=1;
  if (!___EQP(___CAR(gb_cache),gb_param)) {
    ___WORD gb_cache2=___THREAD_DENV_CACHE2_FIELD(gb_thread);
    if (___EQP(___CAR(gb_cache2),gb_param)) {
      ___THREAD_DENV_CACHE2_FIELD(gb_thread)=gb_cache;
      ___THREAD_DENV_CACHE1_FIELD(gb_thread)=gb_cache2;
      gb_cache=gb_cache2;
      gb_slot=2;
    } else {
      ___WORD gb_cache3=___THREAD_DENV_CACHE3_FIELD(gb_thread);
      if (!___EQP(___CAR(gb_cache3),gb_param)) return 0;
      ___THREAD_DENV_CACHE3_FIELD(gb_thread)=gb_cache2;
      ___THREAD_DENV_CACHE2_FIELD(gb_thread)=gb_cache;
      ___THREAD_DENV_CACHE1_FIELD(gb_thread)=gb_cache3;
      gb_cache=gb_cache3;
      gb_slot=3;
    }
  }
  result->value=___CDR(gb_cache);
  result->getter=___VECTORREF(___CLO(gb_param,1),___FIX(3L));
  result->slot=gb_slot;
  GB_PARAMETER_SLOT(gb_slot);
  return 1;
}
#define GB_PARAMETER_TRY(expression) do { \
  if (!___EXPECT_FALSE((___fp-8) < ___ps->stack_trip)) { \
    struct gb_parameter_result gb_answer; \
    if (gb_parameter_lookup(___ps,(expression),&gb_answer)) { \
      ___WORD gb_getter=gb_answer.getter; \
      ___SET_R1(gb_answer.value) \
      GB_PARAMETER_HIT(); \
      ___JUMPGENNOTSAFE(___SET_NARGS(1),gb_getter) \
    } \
  } \
} while (0);
#else
#define GB_PARAMETER_TRY(expression) ((void)0);
#endif
"""


def identity_preamble(coherent_epoch=False, env_lookup=False):
    anchor = '___IMP_DATA(___glo_struct,___G__23__23_make_2d_parameter);'
    branch = '      ___JUMPGENNOTSAFE(___SET_NARGS(1),gb_getter) \\\n'
    if PREAMBLE.count(anchor) != 1 or PREAMBLE.count(branch) != 1:
        raise ValueError('original parameter preamble shape changed')
    result = PREAMBLE.replace(anchor, anchor + '''
___IMP_DATA(___glo_struct,___G__23__23_identity);
___IMP_DATA(___glo_struct,___G_identity);
#ifndef GB_PARAMETER_IDENTITY_HIT
#define GB_PARAMETER_IDENTITY_HIT() ((void)0)
#endif''')
    if env_lookup:
        cache3 = '''      if (!___EQP(___CAR(gb_cache3),gb_param)) return 0;
      ___THREAD_DENV_CACHE3_FIELD(gb_thread)=gb_cache2;
      ___THREAD_DENV_CACHE2_FIELD(gb_thread)=gb_cache;
      ___THREAD_DENV_CACHE1_FIELD(gb_thread)=gb_cache3;
      gb_cache=gb_cache3;
      gb_slot=3;'''
        if result.count(cache3) != 1:
            raise ValueError('original third-slot lookup shape changed')
        result = result.replace(anchor, anchor + '''
___IMP_DATA(___glo_struct,___G__23__23_env_2d_lookup);
#ifndef GB_PARAMETER_ENV_HIT
#define GB_PARAMETER_ENV_HIT(bound) ((void)0)
#endif''')
        result = result.replace(cache3, '''      if (!___EQP(___CAR(gb_cache3),gb_param)) {
        if (___GLOCELL(___G__23__23_env_2d_lookup.val)!=___PRMCELL(___G__23__23_env_2d_lookup.prm)) return 0;
        ___WORD gb_env=___DENV_LOCAL_FIELD(___THREAD_DENV_FIELD(gb_thread));
        ___WORD gb_hash=___VECTORREF(___CLO(gb_param,1),___FIX(1));
        ___WORD gb_found=___FAL;
        if (!___FIXNUMP(gb_hash)) return 0;
        for (int gb_depth=0; gb_env!=___NUL; ++gb_depth) {
          if (gb_depth>=128 || !___VECTORP(gb_env) || ___INT(___VECTORLENGTH(gb_env))<3) return 0;
          ___WORD gb_pair=___ENV_PARAM_VAL_FIELD(gb_env);
          if (!___PAIRP(gb_pair)) return 0;
          ___WORD gb_other=___CAR(gb_pair);
          if (!___CLOSUREP(gb_other) || ___LABEL_ENTRY_GET(gb_other)!=
              ___PRMCELL(___G__23__23_make_2d_parameter.prm)+(5*___LABEL_SIZE*___WS)) return 0;
          ___WORD gb_other_hash=___VECTORREF(___CLO(gb_other,1),___FIX(1));
          if (!___FIXNUMP(gb_other_hash)) return 0;
          if (___FIXLT(gb_hash,gb_other_hash)) gb_env=___ENV_LEFT_FIELD(gb_env);
          else if (___FIXLT(gb_other_hash,gb_hash) || !___EQP(gb_other,gb_param)) gb_env=___ENV_RIGHT_FIELD(gb_env);
          else { gb_found=gb_pair; break; }
        }
        if (gb_found==___FAL) {
          result->value=___VECTORREF(___CLO(gb_param,1),___FIX(0));
          result->getter=___VECTORREF(___CLO(gb_param,1),___FIX(3));
          result->slot=0;
          GB_PARAMETER_ENV_HIT(0);
          return 1;
        }
        ___THREAD_DENV_CACHE3_FIELD(gb_thread)=gb_cache2;
        ___THREAD_DENV_CACHE2_FIELD(gb_thread)=gb_cache;
        ___THREAD_DENV_CACHE1_FIELD(gb_thread)=gb_found;
        gb_cache=gb_found;
        gb_slot=4;
        GB_PARAMETER_ENV_HIT(1);
      } else {
        ___THREAD_DENV_CACHE3_FIELD(gb_thread)=gb_cache2;
        ___THREAD_DENV_CACHE2_FIELD(gb_thread)=gb_cache;
        ___THREAD_DENV_CACHE1_FIELD(gb_thread)=gb_cache3;
        gb_cache=gb_cache3;
        gb_slot=3;
      }''')
        result = result.replace('  GB_PARAMETER_SLOT(gb_slot);', '  if (gb_slot<=3) GB_PARAMETER_SLOT(gb_slot);')
    if coherent_epoch:
        lookup = '      ___WORD gb_getter=gb_answer.getter; \\\n'
        if result.count(lookup) != 1:
            raise ValueError('original lookup shape changed')
        # Slot swaps affect cached reads of the thread, not unrelated objects.
        result = result.replace(lookup,
            '      if (gb_answer.slot>=2) GB_TRACE_THREAD_INVALIDATE_AT(65535); \\\n' + lookup)
    return result.replace(branch, r'''      if (gb_getter==___PRMCELL(___G__23__23_identity.prm) || \
          gb_getter==___PRMCELL(___G_identity.prm)) { \
        ___SELF=gb_getter; \
        ___SET_NARGS(1) \
        GB_PARAMETER_IDENTITY_HIT(); \
        ___JUMPRET(___R0) \
      } \
''' + branch)
