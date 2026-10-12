/* ---------- Kod bloklarini bo'yash ----------
 *
 * Tashqi kutubxonasiz. Sabab: highlight.js ~120 KB, prism ~40 KB, ikkalasi
 * ham sayt ochilishini sekinlashtiradi. Darsliklardagi 2732 ta kod blokining
 * 93% i uchta tilda (python 1145, bash 776, sql 629), qolgani esa umumiy
 * qoidalar bilan yetarlicha o'qiladi.
 *
 * XAVFSIZLIK
 * ==========
 * Bo'yash XOM matn ustida bajariladi, HTML esa har bo'lak uchun ALOHIDA
 * qochiriladi (`esc`). Ya'ni kod ichidagi `<script>` hech qachon teg bo'lib
 * qolmaydi. Avval qochirib, keyin bo'yash MUMKIN EMAS edi: `&quot;` kabi
 * ketma-ketliklar satr sifatida noto'g'ri tanilardi.
 *
 * USUL
 * ====
 * Har til uchun bitta katta muqobil (alternation) ifoda. Matn ketma-ket
 * o'qiladi, mos kelgan bo'lak bo'yaladi, oradagi matn shunchaki qochiriladi.
 * Bir marta o'tiladi — uzun fayllarda ham tez.
 */
(function (root) {
  'use strict';

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  var PY_KW = 'False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield|self|cls';
  var SH_KW = 'if|then|else|elif|fi|for|while|do|done|case|esac|in|function|return|export|local|source|alias|set|unset|echo|cd|exit';
  var SQL_KW = 'SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|ALTER|DROP|INDEX|VIEW|JOIN|LEFT|RIGHT|INNER|OUTER|FULL|ON|AS|AND|OR|NOT|NULL|IS|IN|LIKE|BETWEEN|GROUP|BY|ORDER|HAVING|LIMIT|OFFSET|DISTINCT|COUNT|SUM|AVG|MIN|MAX|PRIMARY|KEY|FOREIGN|REFERENCES|DEFAULT|UNIQUE|CONSTRAINT|CASCADE|BEGIN|COMMIT|ROLLBACK|WITH|CASE|WHEN|THEN|END|EXISTS|UNION|ALL|ADD|COLUMN|RETURNING|CONFLICT|DO|NOTHING';

  /* Har element: [nom, ifoda]. Tartib MUHIM — izoh va satr birinchi
     bo'lishi kerak, aks holda ular ichidagi kalit so'zlar bo'yalardi. */
  var RULES = {
    python: [
      ['com', /#[^\n]*/],
      ['str', /[frbu]{0,2}("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')/],
      ['dec', /@[A-Za-z_][\w.]*/],
      ['kw',  new RegExp('\\b(?:' + PY_KW + ')\\b')],
      ['def', /(?:\bdef\s+|\bclass\s+)[A-Za-z_]\w*/],
      ['num', /\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?\b/],
      ['fn',  /\b[A-Za-z_]\w*(?=\s*\()/]
    ],
    bash: [
      ['com', /#[^\n]*/],
      ['str', /"(?:\\.|[^"\\])*"|'[^']*'/],
      ['var', /\$\{[^}]*\}|\$[A-Za-z_]\w*/],
      ['kw',  new RegExp('\\b(?:' + SH_KW + ')\\b')],
      ['opt', /(?:^|\s)--?[A-Za-z][\w-]*/],
      ['num', /\b\d+\b/]
    ],
    sql: [
      ['com', /--[^\n]*|\/\*[\s\S]*?\*\//],
      ['str', /'(?:''|[^'])*'/],
      ['kw',  new RegExp('\\b(?:' + SQL_KW + ')\\b', 'i')],
      ['num', /\b\d+(?:\.\d+)?\b/],
      ['fn',  /\b[A-Za-z_]\w*(?=\s*\()/]
    ],
    /* Qolgan tillar: izoh, satr, son — shuning o'zi o'qishni ancha
       yengillashtiradi, har til uchun alohida qoida yozish esa
       foydasiga yarasha emas. */
    generic: [
      ['com', /#[^\n]*|\/\/[^\n]*|<!--[\s\S]*?-->|\/\*[\s\S]*?\*\//],
      ['str', /"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`/],
      ['num', /\b\d+(?:\.\d+)?\b/]
    ]
  };

  var ALIAS = {
    py: 'python', python3: 'python', django: 'python',
    sh: 'bash', shell: 'bash', console: 'bash', zsh: 'bash', dockerfile: 'bash',
    postgres: 'sql', postgresql: 'sql', psql: 'sql', mysql: 'sql'
  };

  /* Ifoda ichida nechta qamrab oluvchi guruh borligini sanaydi.

     Bu SHART: qoidalar ichida o'z guruhlari bo'lishi mumkin (masalan
     python satrida `[frbu]{0,2}(...)`), va ular hisobga olinmasa guruh
     raqamlari surilib ketadi — natijada mos kelgan bo'lakka BOSHQA qoida
     nomi berilardi. Aynan shu nosozlik sinovda tutilgan: `import` "kalit
     so'z" o'rniga "satr" deb bo'yalardi.

     Usul: ifodaga bo'sh muqobil qo'shiladi, shunda u har doim mos keladi
     va `exec` natijasining uzunligi guruhlar sonini beradi. */
  function groupCount(re) {
    return new RegExp(re.source + '|').exec('').length - 1;
  }

  var cache = {};
  function compiled(lang) {
    if (cache[lang]) return cache[lang];
    var rules = RULES[lang] || RULES.generic;
    var parts = [], slots = [], idx = 1;
    rules.forEach(function (r) {
      parts.push('(' + r[1].source + ')');
      slots.push({ name: r[0], at: idx });
      idx += 1 + groupCount(r[1]);   // o'z guruhi + ichkilari
    });
    var flags = 'g';
    /* SQL kalit so'zlari katta-kichik harfda ham yoziladi. */
    if (lang === 'sql') flags += 'i';
    cache[lang] = { slots: slots, re: new RegExp(parts.join('|'), flags) };
    return cache[lang];
  }

  function norm(lang) {
    var l = String(lang || '').toLowerCase().trim();
    l = ALIAS[l] || l;
    return RULES[l] ? l : 'generic';
  }

  /* Xom kodni bo'yalgan HTML ga aylantiradi. */
  function code(lang, raw) {
    var text = String(raw == null ? '' : raw);
    var c = compiled(norm(lang));
    var out = '', last = 0, m;
    c.re.lastIndex = 0;
    while ((m = c.re.exec(text)) !== null) {
      /* Bo'sh moslik cheksiz aylanishga olib keladi — himoya. */
      if (m[0] === '') { c.re.lastIndex++; continue; }
      out += esc(text.slice(last, m.index));
      var cls = 'generic';
      for (var g = 0; g < c.slots.length; g++) {
        if (m[c.slots[g].at] !== undefined) { cls = c.slots[g].name; break; }
      }
      out += '<span class="hl-' + cls + '">' + esc(m[0]) + '</span>';
      last = m.index + m[0].length;
    }
    out += esc(text.slice(last));
    return out;
  }

  root.Hilite = { code: code, esc: esc };
})(window);
