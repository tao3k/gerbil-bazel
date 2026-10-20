/* Prototype only: no stack arguments or GC can occur in this fast branch. */
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && ___NB_ARG_REGS == 3
#define ___GET_REST_DARWIN(lbl,nb_req,nb_opt,nb_key) \
{ \
  if (___ps->na >= 0) { \
    ___WORD gb_na = ___ps->na; \
    if ((nb_opt) == 0 && (nb_key) == 0 && (nb_req) <= 2 && \
        gb_na >= (nb_req) && gb_na <= 3 && \
        ___hp + (gb_na - (nb_req)) * (___PAIR_SIZE + ___PAIR_BODY) <= ___ps->heap_limit) { \
      ___SCMOBJ gb_list = ___NUL; \
      if (gb_na == 3) gb_list = ___CONS(___R3, gb_list); \
      if (gb_na >= 2 && (nb_req) < 2) gb_list = ___CONS(___R2, gb_list); \
      if (gb_na >= 1 && (nb_req) < 1) gb_list = ___CONS(___R1, gb_list); \
      switch (nb_req) { \
        case 0: ___SET_R1(gb_list) break; \
        case 1: ___SET_R2(gb_list) break; \
        case 2: ___SET_R3(gb_list) break; \
      } \
      ___ps->na = -1; \
    } else { \
      ___GET_REST(lbl,nb_req,nb_opt,nb_key) \
    } \
  } \
}
#else
#define ___GET_REST_DARWIN(lbl,nb_req,nb_opt,nb_key) ___GET_REST(lbl,nb_req,nb_opt,nb_key)
#endif
