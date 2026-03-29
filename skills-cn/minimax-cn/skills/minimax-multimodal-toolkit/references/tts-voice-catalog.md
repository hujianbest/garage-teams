# TTS 语音目录

## 内容

- [语音选择指南](#voice-selection-guide)
- [按语言分类的系统语音](#system-voices-by-language)
- [语音参数](#voice-parameters)
- [自定义声音](#custom-voices)

---

## 语音选型指南

### 决策流程```
Content type?
├── Narration / Audiobook  → audiobook_female_1, audiobook_male_1
├── News / Announcement    → Chinese (Mandarin)_News_Anchor, Chinese (Mandarin)_Male_Announcer
├── Documentary            → doc_commentary
└── Other                  → Select by: Gender → Age → Language → Personality
```### 推荐专业声音

|场景|推荐|特点 |
|----------|-------------|-----------------|
|旁白/有声读物| `有声书_女_1`、`有声书_男_1` |清晰的发音、良好的节奏、持续的表演 |
|新闻/公告 | `中文（普通话）_新闻_主播`、`中文（普通话）_男_播音员` |权威、专业节奏 |
|纪录片| `doc_commentary` |专业、清晰、一致 |

### 选择优先级

1. **性别**（必配）——男性角色配男性声音，女性角色配女性声音
2. **年龄** — 儿童/青少年/成人/老人
3. **语言**（必须与内容语言匹配）
4. **个性/语气** — 从匹配的候选人中选择最适合的人

---

## 按语言分类的系统语音

性别：M = 男，F = 女，N = 中性/角色
年龄：C = 儿童、Y = 青少年、A = 成人、E = 老年人

### 普通话

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `男qn情色` | 青涩青年 |中号 |是 |年轻，缺乏经验|校园，成长|
| `男-qn-badao` | 霸道青年 |中号 |是 |傲慢、霸道|剧情、爱情 |
| `男qn大学生` | 青年大学生 |中号 |是 |大学生|校园，教育 |
| `男-qn-jingying` | 精英青年 |中号 |一个 |精英，雄心勃勃|商业、专业|
| `女少女` | 少女 | F |是 |年轻处女|浪漫、青春|
| `女宇杰` | 御姐 | F |一个 |成熟、优雅|浪漫、专业|
| `女-成书` | 职业女性 | F |一个 |成熟、可靠|精密、新闻|
| `女天美` | 魅力女性 | F |一个 |甜美可人|柔软、温柔|
| `聪明男孩` | 男聪明童 |中号 | C |聪明、机智|儿童教育 |
| `可爱的男孩` | 可爱男童 |中号 | C |可爱|儿童、动画 |
| `可爱的女孩` | 萌萌女童 | F | C |可爱、甜美|儿童故事|
|卡通猪 卡通猪小琪 |尼 | C |卡通人物|动画、喜剧 |
| `bingjiao_didi` | 病娇弟弟 |中号 |是 |傲娇哥哥|浪漫、性格|
| `junlang_nanyou` | 俊朗男友 |中号 |是 |帅气男友|浪漫、约会 |
| `chunzhen_xuedi` | 纯真学弟 |中号 |是 |纯真少年|校园，青春|
| `lengdan_xiongzhang` | 冷淡学长 |中号 |是 |酷前辈|校园、浪漫|
| `badao_shaoye` | 霸道少爷 |中号 |一个 |嚣张少爷|戏剧、人物 |
| `tianxin_xiaoling` | 甜心小玲 | F |是 |甜甜小玲|角色、动画|
| `qiaopi_mengmei` | 俏皮萌妹 | F |是 |俏皮可爱的女孩|喜剧，轻松|
| `wumei_yujie` | 媚媚御姐 | F |一个 |迷人的成熟女人|浪漫、成熟|
| `diadia_xuemei` | 嗲嗲学妹 | F |是 |轻浮的小女孩|浪漫、约会 |
| `danya_xuejie` | 淡雅学姐 | F |是 |优雅高级女孩|校园、浪漫|
| 《傲慢小姐》| 嚣张小姐| F |一个 |傲慢的小姐|戏剧、人物|
| `机器人装甲` | 机械战甲 |尼 |一个 |机器人装甲|科幻、游戏|
| `有声书_男性_1` | 有声书男1 |中号 |一个 |热情、引人入胜的叙述者 |有声读物、故事 |
| `有声书_女性_1` | 有声书女1 | F |一个 |温柔、富有表现力的叙述者 |有声读物、故事 |
| `doc_commentary` | 文献解说 |中号 |一个 |专业解说员|纪录片|
| `中文（普通话）_新闻_主播` | 新闻女声 | F |一个 |新闻主播|新闻、广播 |
| `中文（普通话）_男_播音员` | 播报男声 |中号 |一个 |男主播|公告 |
| `中文（普通话）_Radio_Host` | 电台男主播|中号 |一个 |电台主持人|播客、广播 |
| `中文（普通话）_可靠_执行力` | 沉稳高管 |中号 |一个 |可靠的执行官 |企业、商业|
| `中文（普通话）_绅士` | 温润男声 |中号 |一个 |温柔、精致|旁白、讲故事 |
| `中文（普通话）_无拘无束的年轻人` | 不羁青年 |中号 |是 |无拘无束、随性|娱乐 |
| `中文（普通话）_南方年轻人` | 南方小哥 |中号 |是 |南方口音|地域性、休闲性|
| `中文（普通话）_温柔_青春` | 温润青年 |中号 |是 |温柔的年轻人|叙述，平静|
| `中文（普通话）_真诚_成人` | 真诚青年|中号 |是 |真诚、真诚|诚实、真诚|
| `中文（普通话）_Straightforward_Boy` | 率真弟弟 |中号 |是 |弗兰克，直接|休闲、直接|
| `中文（普通话）_纯心肠_男孩` | 清水邻家弟弟 |中号 |是 |纯洁的邻居|纯真、健康 |
| `中文（普通话）_固执_朋友` | 嘴硬竹马 |中号 |是 |顽固的儿时好友|戏剧、人物|
| `中文（普通话）_Lyrical_Voice` | 抒情男声 ​​|中号 |一个 |抒情、歌唱|音乐、歌唱|
| `中文（普通话）_成熟_女人` | 傲娇御姐| F |一个 |傲娇成熟女人|浪漫、性格|
| `中文（普通话）_Sweet_Lady` | 闪耀女声 | F |一个 |甜美女士|柔软、温柔|| `Chinese (Mandarin)_Warm_Bestie` | 温暖闺蜜 | F | A | Warm bestie | Friendly, supportive |
| `Chinese (Mandarin)_Warm_Girl` | 温暖少女 | F | Y | Warm young girl | Friendly, supportive |
| `Chinese (Mandarin)_Soft_Girl` | 柔和少女 | F | Y | Soft, gentle | Calm, soothing |
| `Chinese (Mandarin)_Crisp_Girl` | 清脆少女 | F | Y | Crisp, clear | Bright, clear |
| `Chinese (Mandarin)_Gentle_Senior` | 温柔学姐 | F | Y | Gentle senior girl | Campus, supportive |
| `Chinese (Mandarin)_Wise_Women` | 阅历姐姐 | F | A | Experienced, wise | Advice, guidance |
| `Chinese (Mandarin)_HK_Flight_Attendant` | 港普空姐 | F | A | HK accent flight attendant | Regional, entertainment |
| `Chinese (Mandarin)_Cute_Spirit` | 憨憨萌兽 | N | C | Cute cartoon spirit | Animations, children's |
| `Chinese (Mandarin)_Humorous_Elder` | 搞笑大爷 | M | E | Humorous old man | Comedy, entertainment |
| `Chinese (Mandarin)_Kind-hearted_Elder` | 花甲奶奶 | F | E | Kind elderly lady | Stories, warm |
| `Chinese (Mandarin)_Kind-hearted_Antie` | 热心大婶 | F | E | Kind-hearted auntie | Warm, friendly |

### Chinese Cantonese (粤语)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Cantonese_ProfessionalHost（F)` | 专业女主持 | F | A | Professional host | Broadcasts, hosting |
| `Cantonese_GentleLady` | 温柔女声 | F | A | Gentle female | Soft, warm |
| `Cantonese_ProfessionalHost（M)` | 专业男主持 | M | A | Professional host | Broadcasts, hosting |
| `Cantonese_PlayfulMan` | 活泼男声 | M | A | Playful male | Entertainment, casual |
| `Cantonese_CuteGirl` | 可爱女孩 | F | C | Cute girl | Children's, animations |
| `Cantonese_KindWoman` | 善良女声 | F | A | Kind female | Warm, friendly |

### English

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `English_Trustworthy_Man` | Trustworthy Man | M | A | Reliable, sincere | Business, narration |
| `English_Graceful_Lady` | Graceful Lady | F | A | Elegant, refined | Formal, professional |
| `English_Aussie_Bloke` | Aussie Bloke | M | A | Casual Australian | Casual, entertainment |
| `English_Whispering_girl` | Whispering Girl | F | Y | Soft whisper | Romance, intimate |
| `English_Diligent_Man` | Diligent Man | M | A | Earnest, hardworking | Motivational, educational |
| `English_Gentle-voiced_man` | Gentle-voiced Man | M | E | Soft-spoken, kind | Calm, supportive |
| `English_Sweet_Girl` | Sweet Girl | F | C | Sweet, innocent | Children's, friendly |
| `Charming_Lady` | Charming Lady | F | A | Elegant, sophisticated | Professional, romance |
| `Attractive_Girl` | Attractive Girl | F | Y | Engaging female | Entertainment, marketing |
| `Serene_Woman` | Serene Woman | F | A | Calm, peaceful | Meditation, relaxation |
| `Santa_Claus` | Santa Claus | M | E | Festive, jolly | Holiday, children's |
| `Charming_Santa` | Charming Santa | M | E | Smooth, charismatic | Holiday, entertainment |
| `Grinch` | Grinch | M | A | Whiny, mischievous | Comedy, holiday |
| `Rudolph` | Rudolph | N | C | Cute, nasal reindeer | Children's, holiday |
| `Arnold` | Arnold | M | A | Deep, robotic | Sci-fi, action |
| `Cute_Elf` | Cute Elf | N | C | Playful, tiny elf | Fantasy, children's |

### Japanese (日本语)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Japanese_IntellectualSenior` | Intellectual Senior | M | E | Wise, knowledgeable | Narration, educational |
| `Japanese_DecisivePrincess` | Decisive Princess | F | A | Confident, royal | Animation, games |
| `Japanese_LoyalKnight` | Loyal Knight | M | A | Brave, faithful | Fantasy, games |
| `Japanese_DominantMan` | Dominant Man | M | A | Powerful, commanding | Action, leadership |
| `Japanese_SeriousCommander` | Serious Commander | M | A | Stern, authoritative | Military, games |
| `Japanese_ColdQueen` | Cold Queen | F | A | Distant, majestic | Drama, fantasy |
| `Japanese_DependableWoman` | Dependable Woman | F | A | Reliable, supportive | Guidance |
| `Japanese_GentleButler` | Gentle Butler | M | A | Polite, refined | Comedy, animation |
| `Japanese_KindLady` | Kind Lady | F | A | Warm, gentle | Comforting |
| `Japanese_CalmLady` | Calm Lady | F | A | Composed, serene | Meditation, relaxation |
| `Japanese_OptimisticYouth` | Optimistic Youth | M | Y | Cheerful, positive | Youth, motivation |
| `Japanese_GenerousIzakayaOwner` | Generous Izakaya Owner | M | A | Friendly, welcoming | Casual, comedy || `日本_运动学生` |运动型学生|中号 |是 |精力充沛，运动型 |运动、青少年|
| `日本人_InnocentBoy` |天真无邪的男孩|中号 | C |纯洁、天真|儿童 |
| `日本_GracefulMaiden` |优雅少女| F |是 |优雅、温柔|浪漫、戏剧 |

### 韩语 (한국어)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `韩国_SweetGirl` |甜美女孩| F | C |甜美可爱|儿童、浪漫|
| `韩国_开朗男友` |开朗的男朋友|中号 |是 |精力充沛，有爱心|浪漫、约会 |
| `韩国_迷人妹妹` |妖娆姐姐| F |一个 |迷人、迷人 |家庭、戏剧 |
| `韩国_ShyGirl` |害羞的女孩| F |是 |胆怯、矜持|喜剧、爱情 |
| `韩国_可靠姐姐` |可靠姐姐| F |一个 |值得信赖、值得信赖 |指导|
| `Korean_StrictBoss` |严格的老板|中号 |一个 |权威、苛求|商业、戏剧 |
| `韩国_野蛮女孩` |野蛮女孩 | F |是 |大胆、机智|喜剧、娱乐 |
| `韩国_ChildhoodFriendGirl` |儿时朋友女孩| F |是 |熟悉、友善|浪漫、怀旧|
| `Korean_PlayboyCharmer` |花花公子魅力 |中号 |一个 |圆润、妖艳|浪漫、娱乐|
| `韩国_优雅公主` |优雅公主| F |一个 |雍容华贵 |动画、奇幻 |
| `韩国_勇敢女战士` |勇敢的女战士| F |一个 |勇敢|动作、奇幻 |
| 《韩国勇敢青年》 |勇敢的青春|中号 |是 |英雄 |行动，青春|
| `韩国_CalmLady` |冷静女士| F |一个 |沉稳、平静 |冥想、放松 |
| `韩国_EnthusiasticTeen` |热情的青少年|中号 |是 |兴奋、充满活力|青年|
| `韩国_SoothingLady` |舒缓女士| F |一个 |平静、安慰 |放松 |
| `韩国_知识分子高级` |知识分子高级|中号 |电子|睿智、博学 |教育、解说 |
| `韩国_LonelyWarrior` |孤独的战士|中号 |一个 |孤独、忧郁|剧情、奇幻 |
| '韩国_成熟女士' |成熟女士| F |一个 |精密|专业、戏剧|
| `Korean_InnocentBoy` |天真无邪的男孩|中号 | C |纯洁、天真|儿童 |
| `韩国_魅力姐姐` |迷人姐姐| F |一个 |迷人、令人愉悦 |家庭、浪漫 |
| `Korean_AthleticStudent` |运动学生|中号 |是 |运动、活力 |运动、青少年|
| `韩国_勇敢冒险家` |勇敢的冒险家 |中号 |一个 |勇敢的探险家|冒险、奇幻|
| `韩国_冷静绅士` |冷静的绅士|中号 |一个 |沉稳、精致 |正式、专业|
| `Korean_WiseElf` |聪明的精灵|中号 |电子|古老、神秘 |奇幻、旁白 |
| `Korean_CheerfulCoolJunior` |开朗酷少年|中号 |是 |受欢迎、友好 |青春、娱乐|
| `韩国_果断女王` |果断女王| F |一个 |指挥|剧情、奇幻 |
| `Korean_ColdYoungMan` |冷酷的年轻人|中号 |是 |疏远、疏远|剧情、爱情 |
| `韩国_神秘女孩` |神秘女孩| F |是 |神秘、神秘 |悬疑、剧情 |
| `韩国_QuirkyGirl` |古怪的女孩| F |是 |古怪、独特|喜剧 |
| `Korean_ConsiderateSenior` |体贴的前辈 |中号 |电子|体贴、关怀|温暖、支持|
| `韩国_开朗小妹妹` |性格开朗的小妹妹| F | C |俏皮可爱|家庭、喜剧 |
| `Korean_DominantMan` |主导男人|中号 |一个 |强大，指挥 |领导力、行动 |
| `韩国_空头女孩` |傻女孩 | F |是 |气泡、空间感 |喜剧 |
| `韩国_可靠青年` |可靠的青年|中号 |是 |值得信赖、值得信赖 |支持|
| `韩国_友好大姐姐` |友善的大姐姐| F |一个 |温暖、防护 |家人，支持|
| `韩国_GentleBoss` |温柔的老板|中号 |一个 |善良、善解人意 |业务 |
| `韩国_冷女孩` |冷酷女孩| F |是 |疏远、疏远 |剧情、爱情 |
| `韩国_傲慢女士` |傲慢的女士 | F |一个 |傲慢、骄傲|戏剧、喜剧 |
| `韩国_迷人姐姐` |迷人姐姐| F |一个 |优雅|浪漫、家庭|
| `韩国_知识分子` |知识分子|中号 |一个 |聪明、知识渊博 |教育 |
| `韩国_CaringWoman` |关爱女人| F |一个 |培育|支持、温暖|
| `韩国_WiseTeacher` |智慧老师|中号 |电子|经验丰富 |教育 |
| `韩国_ConfidentBoss` |自信的老板|中号 |一个 |自信、有能力|商业、领导力 |
| `Korean_AthleticGirl` |运动女孩| F |是 |运动、活力 |运动、健身|
| `韩国_占有欲男人` |占有欲强的男人|中号 |一个 |强烈、保护性|浪漫、戏剧 |
| `韩国_GentleWoman` |温柔的女人| F |一个 |说话温柔，善良|冷静|| `Korean_CockyGuy` |自大的家伙|中号 |是 |自信、傲慢|喜剧 |
| `韩国_体贴的女人` |体贴的女人| F |一个 |反思、关怀 |戏剧 |
| 《韩国乐观青年》 |乐观青年|中号 |是 |积极、充满希望|动机|

### 西班牙语 (Español)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `西班牙语_旁白` |旁白|中号 |一个 |专业解说员|纪录片|
| `西班牙语_迷人的故事讲述者` |迷人的讲故事者 |中号 |一个 |引人入胜的叙述者 |有声读物 |
| `Spanish_WiseScholar` |智者学者|中号 |一个 |知识渊博|教育 |
| `Spanish_SereneWoman` |宁静的女人| F |一个 |平静、平和 |放松 |
| `Spanish_MaturePartner` |成熟的合作伙伴|中号 |一个 |精密|浪漫、戏剧 |
| `Spanish_ConfidentWoman` |自信的女人| F |一个 |自信 |专业|
| `Spanish_DeterminedManager` |坚定的经理|中号 |一个 |雄心勃勃，干劲十足|业务 |
| `Spanish_BossyLeader` |专横的领袖 |中号 |一个 |指挥|领导力 |
| `Spanish_ReservedYoungMan` |矜持的年轻人|中号 |是 |安静、内向|戏剧 |
| `Spanish_ThoughtfulMan` |体贴的人|中号 |一个 |反光|教育 |
| `Spanish_RationalMan` |理性人|中号 |一个 |逻辑性、分析性|业务 |
| `Spanish_Deep-tonedMan` |深色调的男人 |中号 |一个 |深沉、共鸣 |指挥|
| `Spanish_Jovialman` |快活的人 |中号 |一个 |性格开朗、友善|娱乐 |
| `Spanish_Steadymentor` |稳定的导师|中号 |一个 |值得信赖的导师|指导|
| `Spanish_ReliableMan` |可靠的人|中号 |一个 |值得信赖|专业|
| `西班牙_浪漫丈夫` |浪漫的丈夫|中号 |一个 |恩爱、浪漫|浪漫|
| `西班牙喜剧演员` |喜剧演员 |中号 |一个 |幽默|喜剧 |
| `西班牙语_辩手` |辩手 |中号 |一个 |有说服力|辩论|
| `Spanish_ToughBoss` |严厉的老板|中号 |一个 |严酷、要求严格|商业、戏剧 |
| `Spanish_AngryMan` |愤怒的人|中号 |一个 |沮丧|戏剧、喜剧 |
| `西班牙_强大的士兵` |强大的士兵|中号 |一个 |坚强、勇敢|军事行动 |
| `Spanish_PassionateWarrior` |热血战士|中号 |一个 |激烈、专注|动作、奇幻 |
| `Spanish_PowerfulVeteran` |实力老将|中号 |一个 |经验丰富 |军事 |
| `Spanish_SensibleManager` |明智的经理 |中号 |一个 |实用|业务 |
| `西班牙_善良的女孩` |善良的女孩| F | C |温暖、慈悲 |儿童 |
| `Spanish_SophisticatedLady` |精致女士| F |一个 |优雅、精致|正式|
| `Spanish_FrankLady` |弗兰克夫人| F |一个 |直接、诚实 |喜剧 |
| `西班牙_挑剔的女主人` |挑剔的女主人| F |一个 |要求严格|喜剧、正剧 |
| `Spanish_Wiselady` |聪明的女士| F |电子|经验丰富、睿智|指导|
| `Spanish_ThoughtfulLady` |体贴的女士| F |一个 |体贴|咨询 |
| `Spanish_AssertiveQueen` |自信的女王 | F |一个 |指挥|剧情、奇幻 |
| `Spanish_CaringGirlfriend` |贴心女友| F |是 |培育|浪漫|
| `Spanish_ChattyGirl` |健谈的女孩 | F |是 |健谈、善于交际 |喜剧 |
| `Spanish_CompellingGirl` |迷人的女孩 | F |是 |有说服力|营销|
| `Spanish_WhimsicalGirl` |异想天开的女孩 | F | C |俏皮、富有想象力|儿童 |
| `Spanish_Intonategirl` |语调女孩| F |是 |音乐、旋律|唱歌|
| `Spanish_SincereTeen` |真诚的青少年 |中号 |是 |诚实、真诚|青年|
| `西班牙_意志坚强的男孩` |意志坚强的男孩|中号 |是 |决心|青春，动力|
| `Spanish_EnergeticBoy` |精力充沛的男孩|中号 | C |活跃、活泼|青少年、运动|
| `Spanish_StrictBoss` |严格的老板|中号 |一个 |严格|业务 |
| `Spanish_HumorousElder` |幽默长辈|中号 |电子|搞笑|喜剧 |
| `Spanish_SereneElder` |宁静长者|中号 |电子|平静、平和|冥想|
| `西班牙语_圣诞老人` |圣诞老人|中号 |电子|节日 |假期 |
| `西班牙语_鲁道夫` |鲁道夫|尼 | C |驯鹿 |假期 |
| `西班牙语_阿诺德` |阿诺德|中号 |一个 |机器人|科幻 |
| `西班牙幽灵` |幽灵|尼 |一个 |诡异|恐怖|
| `Spanish_AnimeCharacter` |动漫人物 |尼 |是 |动漫风格|动画|

### 葡萄牙语 (Português)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `葡萄牙语_旁白` |旁白|中号 |一个 |专业解说员|纪录片|
| `葡萄牙语_迷人的故事讲述者` |迷人的讲故事者 |中号 |一个 |引人入胜的叙述者 |有声读物 || `葡萄牙_WiseScholar` |智者学者|中号 |一个 |知识渊博|教育 |
| `葡萄牙语_深沉的绅士` |声音低沉的绅士|中号 |一个 |深沉、丰富|指挥|
| `葡萄牙人_保留年轻人` |矜持的年轻人|中号 |是 |安静、内向|戏剧 |
| `葡萄牙人_体贴的人` |体贴的人|中号 |一个 |反光|教育 |
| `葡萄牙语_RationalMan` |理性人|中号 |一个 |逻辑|业务 |
| `葡萄牙语_Jovialman` |快活的人 |中号 |一个 |开朗|娱乐 |
| `葡萄牙语_Steadymentor` |稳定的导师|中号 |一个 |值得信赖的导师|指导|
| `葡萄牙_ReliableMan` |可靠的人|中号 |一个 |值得信赖|专业|
| `葡萄牙人_浪漫丈夫` |浪漫的丈夫|中号 |一个 |爱|浪漫|
| `葡萄牙喜剧演员` |喜剧演员 |中号 |一个 |幽默|喜剧 |
| `葡萄牙辩手` |辩手 |中号 |一个 |有说服力|辩论|
| `葡萄牙_ToughBoss` |严厉的老板|中号 |一个 |要求严格|业务 |
| `葡萄牙_StrictBoss` |严格的老板|中号 |一个 |严格|业务 |
| `葡萄牙语_AngryMan` |愤怒的人|中号 |一个 |沮丧|戏剧 |
| 《葡萄牙语教父》 |教父|中号 |一个 |权威|戏剧 |
| `葡萄牙_强大的士兵` |强大的士兵|中号 |一个 |坚强、勇敢|行动|
| `葡萄牙人_强大的退伍军人` |实力老将|中号 |一个 |经验丰富 |军事 |
| `葡萄牙_SensibleManager` |明智的经理 |中号 |一个 |实用|业务 |
| `Portuguese_DeterminedManager` |坚定的经理|中号 |一个 |驱动|业务 |
| `葡萄牙_BossyLeader` |专横的领袖 |中号 |一个 |指挥|领导力 |
| `葡萄牙_CalmLeader` |冷静领袖 |中号 |一个 |沉稳、稳重|领导力 |
| `葡萄牙_FascinatingBoy` |迷人的男孩|中号 |是 |迷人|浪漫|
| `葡萄牙人_意志坚强的男孩` |意志坚强的男孩|中号 |是 |决心|青年|
| `葡萄牙_EnergeticBoy` |精力充沛的男孩|中号 | C |活跃、活泼|青年|
| `葡萄牙_FragileBoy` |脆弱的男孩|中号 |是 |敏感|戏剧 |
| `葡萄牙_成熟伴侣` |成熟的合作伙伴|中号 |一个 |精密|浪漫|
| `葡萄牙语_幽默长者` |幽默长辈|中号 |电子|搞笑|喜剧 |
| `葡萄牙语_SereneElder` |宁静长者|中号 |电子|冷静|冥想|
| `葡萄牙_ConfidentWoman` |自信的女人| F |一个 |自信 |专业|
| `葡萄牙语_SereneWoman` |宁静的女人| F |一个 |平静、平和|放松 |
| `葡萄牙_感伤女士` |感伤女士| F |一个 |情感 |剧情、爱情 |
| `葡萄牙语_Wiselady` |聪明的女士| F |电子|明智|指导|
| `葡萄牙_GorgeousLady` |华丽女士| F |一个 |美丽|浪漫|
| `葡萄牙语_LovelyLady` |可爱的女士| F |一个 |甜美可爱|温暖|
| `葡萄牙_Pompouslady` |浮夸的女士| F |一个 |自视甚高 |喜剧 |
| `葡萄牙魅力女王` |迷人女王| F |一个 |优雅|剧情、奇幻 |
| `葡萄牙_AssertiveQueen` |自信的女王 | F |一个 |指挥|剧情、奇幻 |
| `葡萄牙_CharmingLady` |迷人女士| F |一个 |精密|专业|
| `葡萄牙_鼓舞人心的女士` |鼓舞人心的女士| F |一个 |激励 |动机|
| `葡萄牙_StressedLady` |压力大的女士| F |一个 |着急|喜剧 |
| `葡萄牙语_FrankLady` |弗兰克夫人| F |一个 |直接、诚实 |喜剧 |
| `葡萄牙_挑剔的女主人` |挑剔的女主人| F |一个 |要求严格|喜剧 |
| `葡萄牙_体贴的女士` |体贴的女士| F |一个 |体贴|咨询 |
| `葡萄牙语_温柔老师` |温柔的老师| F |一个 |善良、耐心|教育 |
| 《葡萄牙人_善良的女孩》|善良的女孩| F | C |温暖|儿童 |
| `葡萄牙_SweetGirl` |甜美女孩| F |是 |甜美可爱|浪漫|
| `葡萄牙_AttractiveGirl` |有魅力的女孩 | F |是 |迷人|娱乐 |
| `葡萄牙_PlayfulGirl` |顽皮的女孩| F |是 |爱玩 |喜剧 |
| `葡萄牙语_SmartYoungGirl` |聪明的年轻女孩| F |是 |智能|教育 |
| `葡萄牙_UpsetGirl` |心烦意乱的女孩| F |是 |心疼|戏剧 |
| `葡萄牙_ElegantGirl` |优雅女孩| F |是 |优雅|正式|
| `Portuguese_CompellingGirl` |迷人的女孩 | F |是 |有说服力|营销|
| `葡萄牙_异想天开的女孩` |异想天开的女孩 | F | C |俏皮|儿童 |
| `葡萄牙语_ChattyGirl` |健谈的女孩 | F |是 |健谈|喜剧 |
| `葡萄牙语_NaughtySchoolgirl` |顽皮的女学生| F |是 |淘气|喜剧 |
| `葡萄牙语_SadTeen` |悲伤的青少年| F |是 |忧郁|戏剧 |
| `葡萄牙语_贴心女朋友` |贴心女友| F |是 |培育|浪漫|| `葡萄牙语_友好邻居` |友好邻邦| F |一个 |热情、乐于助人 |社区 |
| `葡萄牙戏剧家` |戏剧家 |中号 |一个 |戏剧 |戏剧 |
| `葡萄牙戏剧演员` |戏剧演员 |中号 |一个 |戏剧性|娱乐 |
| `葡萄牙语_认真的教练` |认真的导师|中号 |一个 |勤奋|培训|
| `葡萄牙语_PlayfulSpirit` |俏皮精神|尼 | C |精神开朗|幻想 |
| `葡萄牙_圣诞老人` |圣诞老人|中号 |电子|节日 |假期 |
| `葡萄牙鲁道夫` |鲁道夫|尼 | C |驯鹿 |假期 |
| `葡萄牙语_阿诺德` |阿诺德|中号 |一个 |机器人|科幻 |
| `葡萄牙_迷人圣诞老人` |迷人的圣诞老人 |中号 |电子|魅力 |假期 |
| `葡萄牙格林奇` |格林奇 |中号 |一个 |淘气|喜剧 |
| `葡萄牙_幽灵` |幽灵|尼 |一个 |诡异|恐怖|
| `葡萄牙语_GrimReaper` |死神|尼 |一个 |黑暗，不祥|恐怖|

### 法语（Français）

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `法语_男性_语音_新` |头脑冷静的人 |中号 |一个 |冷静、理智|专业|
| `法国女新闻主播` |耐心的女主持人 | F |一个 |清晰、耐心 |新闻 |
| `French_CasualMan` |休闲男士 |中号 |一个 |轻松、随意 |休闲 |
| `French_MovieLeadFemale` |电影女主角 | F |一个 |戏剧性、表现力 |戏剧 |
| `French_FemaleAnchor` |女主播| F |一个 |专业主播|新闻 |

### 印度尼西亚语（印度尼西亚语）

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `印度尼西亚_SweetGirl` |甜美女孩| F | C |甜美可爱|儿童 |
| `Indonesian_ReservedYoungMan` |矜持的年轻人|中号 |是 |安静、内向|戏剧 |
| `印度尼西亚_CharmingGirl` |迷人的女孩| F |是 |有吸引力 |浪漫|
| `印度尼西亚_CalmWoman` |冷静的女人| F |一个 |沉着、平和|放松 |
| `Indonesian_ConfidentWoman` |自信的女人| F |一个 |自信 |专业|
| `印度尼西亚_CaringMan` |贴心人|中号 |一个 |培育|家庭|
| `Indonesian_BossyLeader` |专横的领袖 |中号 |一个 |指挥|领导力 |
| `印度尼西亚_DeterminedBoy` |坚定的男孩|中号 |是 |雄心勃勃|青年|
| `印度尼西亚_GentleGirl` |温柔的女孩| F |是 |轻声细语|冷静|

### 德语（德语）

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `German_FriendlyMan` |友善的人|中号 |一个 |热情、平易近人|休闲 |
| `German_SweetLady` |甜美女士| F |一个 |和蔼可亲、善良|温暖|
| `德国_PlayfulMan` |顽皮的男人|中号 |一个 |爱玩 |喜剧 |

### 俄语 (Русский)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `Russian_HandsomeChildhoodFriend` |帅气儿时好友|中号 |是 |迷人|浪漫|
| `Russian_BrightHeroine` |光明女王 | F |一个 |活泼、坚强|戏剧 |
| `Russian_AmbitiousWoman` |雄心勃勃的女人| F |一个 |驱动|专业|
| `Russian_ReliableMan` |可靠的人|中号 |一个 |值得信赖|专业|
| `Russian_CrazyQueen` |疯狂女孩| F |是 |狂野、不可预测|喜剧 |
| `Russian_PessimisticGirl` |悲观的女孩| F |是 |阴沉|喜剧 |
| `Russian_AttractiveGuy` |有魅力的家伙 |中号 |一个 |迷人|浪漫|
| `俄罗斯_脾气暴躁的男孩` |脾气暴躁的男孩|中号 |是 |易怒、脾气暴躁 |喜剧 |

### 意大利语（意大利语）

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `Italian_BraveHeroine` |勇敢的女主角| F |一个 |勇敢|行动|
| `意大利语_旁白` |旁白|中号 |一个 |专业解说员|讲故事|
| `Italian_WanderingSorcerer` |流浪法师|中号 |一个 |神秘|幻想 |
| `Italian_DiligentLeader` |勤奋的领导者|中号 |一个 |勤奋|领导力 |

### 阿拉伯语（阿拉伯语）

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `Arabic_CalmWoman` |冷静的女人| F |一个 |组成|放松 |
| `Arabic_FriendlyGuy` |友善的家伙|中号 |一个 |温暖|休闲 |

### 土耳其语 (Türkçe)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `土耳其_CalmWoman` |冷静的女人| F |一个 |组成|放松 |
| `土耳其_值得信赖的人` |值得信赖的人|中号 |一个 |可靠|专业|

### 乌克兰语 (Українська)|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `乌克兰_CalmWoman` |冷静的女人| F |一个 |组成|放松 |
| `乌克兰_WiseScholar` |智者学者|中号 |一个 |知识渊博|教育 |

### 荷兰语（荷兰）

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `荷兰人善良的女孩` |善良的女孩| F | C |温暖|儿童 |
| `Dutch_bossy_leader` |专横的领袖 |中号 |一个 |指挥|领导力 |

### 越南语 (Tiếng Việt)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `越南_kindheard_girl` |善良的女孩| F | C |温暖|儿童 |

### 泰语 (ภาษาไทย)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `Thai_male_1_sample8` |平静的人 |中号 |一个 |平静、平和|放松 |
| `Thai_male_2_sample2` |友善的人|中号 |一个 |温暖|休闲 |
| `Thai_female_1_sample1` |自信的女人| F |一个 |自信 |专业|
| `Thai_female_2_sample2` |充满活力的女人| F |一个 |活跃、活泼|动机|

### 波兰语（波兰语）

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `Polish_male_1_sample4` |男旁白|中号 |一个 |专业|旁白|
| `Polish_male_2_sample3` |男主播|中号 |一个 |专业|新闻 |
| `Polish_female_1_sample1` |冷静的女人| F |一个 |组成|放松 |
| `Polish_female_2_sample3` |休闲女人| F |一个 |轻松|休闲 |

### 罗马尼亚语 (Română)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `Romanian_male_1_sample2` |可靠的人|中号 |一个 |值得信赖|专业|
| `Romanian_male_2_sample1` |活力青年 |中号 |是 |活跃、活泼|青年|
| `Romanian_female_1_sample4` |乐观青年| F |是 |积极|动机|
| `Romanian_female_2_sample1` |温柔的女人| F |一个 |轻声细语|冷静|

### 希腊语 (Ελληνικά)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `greek_male_1a_v1` |贴心导师|中号 |一个 |反思、明智 |指导|
| `Greek_female_1_sample1` |温柔女士| F |一个 |轻声细语|冷静|
| `Greek_female_2_sample3` |邻家女孩 | F |是 |友善 |休闲 |

### 捷克语（捷克）

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `czech_male_1_v1` |放心的演讲者 |中号 |一个 |自信|演示 |
| `czech_female_5_v7` |坚定的叙述者| F |一个 |可靠|讲故事|
| `czech_female_2_v2` |优雅女士| F |一个 |优雅|正式|

### 芬兰语 (Suomi)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `finnish_male_3_v1` |乐观的男人|中号 |一个 |开朗|动机|
| `finnish_male_1_v2` |友善的男孩|中号 |是 |温暖|儿童 |
| `finnish_female_4_v1` |自信的女人| F |一个 |自信|专业|

### 印地语 (हिन्दी)

|语音 ID |名称 | G |年龄 |描述 |最适合 |
|----------|------|---|-----|-------------|----------|
| `hindi_male_1_v2` |值得信赖的顾问|中号 |一个 |可靠、睿智|指导|
| `hindi_female_2_v1` |宁静的女人| F |一个 |平静、平和|冥想|
| `hindi_female_1_v2` |新闻主播 | F |一个 |专业|新闻 |

---

## 语音参数

### 语音设置```python
from scripts.tts.utils import VoiceSetting

voice = VoiceSetting(
    voice_id="male-qn-qingse",
    speed=1.0,       # 0.5–2.0 (default 1.0)
    volume=1.0,      # 0.1–10.0 (default 1.0)
    pitch=0,         # -12 to +12 (default 0)
    emotion="",      # Leave empty for speech-2.8 auto-matching (recommended)
)
```### 速度

|价值|效果|
|--------|--------|
| 0.75 | 0.75较慢、刻意（新闻、教程）|
| 1.0 |正常配速|
| 1.25 | 1.25稍微快一点（精力充沛）|
| 1.5+ |快速（时间敏感）|

### 情感

|价值|描述 |模型支持 |
|--------|-------------|---------------|
| *（空）* |从文本自动匹配 |语音2.8（推荐）|
| `快乐` |开朗、乐观|全部 |
| `悲伤` |忧郁、忧郁|全部 |
| `生气` |紧张、沮丧 |全部 |
| `害怕` |着急、紧张|全部 |
| `厌恶` |被击退|全部 |
| `惊讶` |惊讶 |全部 |
| `冷静` |中性色调|全部 |
| `流利` |自然、活泼|仅语音2.6 |
| `耳语` |柔软、温柔|仅语音2.6 |

---

## 自定义声音

### 语音克隆

从音频样本创建自定义声音：
- 来源：10s–5min，mp3/wav/m4a，≤20MB，清晰单扬声器
- 最佳：30-60 秒不同语调的干净语音

### 声音设计

从文本描述生成声音：
- 包括：性别、年龄、声音特征、语气、用例
- 示例：“温暖、祖母般的声音，节奏轻柔，非常适合睡前故事”

如果不与 TTS 一起使用，自定义语音将在 7 天后过期。列出所有声音：`python script/tts/generate_voice.py list-voices`