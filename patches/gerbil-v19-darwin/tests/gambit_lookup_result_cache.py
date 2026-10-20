"""Bounded experimental D1510 host cache; not generic compiler admission."""
import re

from gambit_binding_facts import GUARD

WRITES = ('STORE_WORD', 'STORE_WORD_FX', 'GCHASHTABLEFIELDSET',
          'GCHASHTABLESET', 'GCHASHTABLEUNION', 'GCHASHTABLEFIND', 'GCHASHTABLEREHASH')

CACHE = r'''
struct gb_lookup_record { ___WORD table,key,value; unsigned long long epoch; };
static struct gb_lookup_record gb_lookup_records[2][64];
static unsigned long long gb_lookup_generation=1;
static int gb_lookup_dirty=1;
#define GB_LOOKUP_RESET gb_lookup_dirty=1;
static ___WORD __attribute__((noinline,optimize("O3")))
gb_lookup_cached(unsigned int site,___WORD table,___WORD key) {
  unsigned long long hash=(unsigned long long)table;
  hash=(hash>>4)^((unsigned long long)key>>3)^((unsigned long long)key>>13);
  struct gb_lookup_record *slot=&gb_lookup_records[site][hash&63];
  GB_LOOKUP_EVENT(site,0);
  if (gb_lookup_dirty) {
    if (++gb_lookup_generation==0) {
      unsigned int s,i;
      for (s=0;s<2;++s) for (i=0;i<64;++i) gb_lookup_records[s][i].epoch=0;
      gb_lookup_generation=1;
    }
    gb_lookup_dirty=0;
  }
  /* A lazy rehash is observable work and must execute even on a cached pair. */
  if (!___FIXZEROP(___FIXAND(___GCHASHTABLE_FLAGS_FIELD(table),___FIX(___GCHASHTABLE_FLAG_KEY_MOVED)))) {
    gb_lookup_dirty=1;
    GB_LOOKUP_EVENT(site,2);
    return ___GCHASHTABLEREF(table,key);
  }
  if (slot->epoch==gb_lookup_generation && slot->table==table && slot->key==key) {
    GB_LOOKUP_EVENT(site,1);
    return slot->value;
  }
  GB_LOOKUP_EVENT(site,2);
  ___WORD value=___GCHASHTABLEREF(table,key);
  slot->table=table; slot->key=key; slot->value=value; slot->epoch=gb_lookup_generation;
  return value;
}
'''


def write_hooks(header):
    hooks = ('#undef ___EXPR\n#define ___EXPR(x) '
             'do { GB_LOOKUP_RESET x; GB_LOOKUP_RESET } while (0);\n')
    for name in WRITES:
        found = re.findall(r'^#define ___'+name+r'\(([^\n]*?)\)([^\n]*)$', header, re.M)
        if len(found) != 1 or '\\' in found[0][1]:
            raise ValueError('single-line original write required: '+name)
        args, body = found[0]
        hooks += ('#undef ___'+name+'\n#define ___'+name+'('+args+') '
                  '({ __auto_type gb_write_value=('+body.strip().rstrip(';')+'); '
                  'GB_LOOKUP_RESET gb_write_value; })\n')
    return hooks


def inject(code, header, diagnostic=False):
    if 'gb_lookup_cached' in code:
        raise ValueError('already injected')
    if code.count('___BEGIN_M_COD') != 1 or code.count('___END_M_COD') != 1:
        raise ValueError('one original coalesced host required')
    if '___BEGIN_CFUN' in code or '___CFUN_OOL' in code:
        raise ValueError('opaque foreign bodies need separate admission')
    needle = '___WORD gb_t36=(___GCHASHTABLEREF(gb_t32,gb_in2));'
    if code.count(needle) != 3:
        raise ValueError('original lookup envelope changed')
    for event, site in enumerate((7, 11)):
        start = code.index(' gb_trace_native_'+str(site)+'(')
        stop = code.index('\n#endif', start)
        block = code[start:stop]
        if block.count(needle) != 1:
            raise ValueError('original helper lookup required')
        block = block.replace(needle, '___WORD gb_t36=(gb_lookup_cached('
                              +str(event)+',gb_t32,gb_in2));')
        code = code[:start]+block+code[stop:]
    code, count = re.subn(r'(?m)^(#define ___MR_ALL [^\n]*)$',
                         lambda m: m[1]+' GB_LOOKUP_RESET', code)
    if count != 23:
        raise ValueError('all original state reload definitions required')
    event = ('extern unsigned long long gb_diag_attempts[16],gb_diag_hits[16];\n'
             '#define GB_LOOKUP_EVENT(s,k) ((k)==0 ? (void)++gb_diag_attempts[s] : '
             '(k)==1 ? (void)++gb_diag_hits[s] : (void)++gb_diag_attempts[(s)+2])\n'
             if diagnostic else '#define GB_LOOKUP_EVENT(s,k) ((void)0)\n')
    prefix = ('#if '+GUARD+'\n'+event+CACHE+write_hooks(header)+
              '#else\n#define GB_LOOKUP_RESET\n'
              '#define gb_lookup_cached(s,t,k) ___GCHASHTABLEREF(t,k)\n#endif\n')
    insertion = code.index('struct gb_trace_native_7_result')
    insertion = code.rfind('#if ', 0, insertion)
    return code[:insertion]+prefix+code[insertion:], dict(
        sites=[7, 11], slotsPerSite=64, reloadDefinitions=count,
        knownWriteHooks=list(WRITES), statementFence=True, lazyDirtyMarker=True,
        scope='original-host-experiment-not-generic-mutation-or-ffi-admission',
        diagnosticOnly=diagnostic)
