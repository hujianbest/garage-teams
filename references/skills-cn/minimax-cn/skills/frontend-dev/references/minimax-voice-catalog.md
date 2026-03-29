# MiniMax 语音目录

MiniMax 语音 API 中所有可用语音的完整参考。

## 内容

- [语音推荐](#voice-recommendation) - 按内容类型和特征查找语音
- [系统语音列表（按语言分类）](#system-voices-list-categorized-by-language) - 按语言分类的完整语音数据库
- [语音参数](#voice-parameters) - 配置语音设置（速度、音量、音调、情绪）
- [自定义语音](#custom-voices) - 语音克隆和语音设计选项
- [语音比较表](#voice-comparison-table) - 快速参考比较
- [语音 ID 快速参考](#voice-ids-for-quick-reference) - 最流行的语音一目了然

---

## 1. 如何选择声音

选择声音时，请遵循这个两步决策过程，以确保声音与角色的场景、性别、年龄和语言相匹配。

### 步骤1：确定使用场景

首先，确定您的内容是否属于**第 2.1 节**中列出的**三个专业领域**之一：

|专业领域|示例 |
|---|---|
| **讲故事中的旁白和叙述者** |适合有声读物、小说旁白、讲故事中的叙述者 |
| **News & Announcements** |适用于新闻广播、正式公告、新闻稿|
| **纪录片** |适合纪实解说、解说、教育片|

**如果您的内容与以下专业领域之一匹配：**
→ 优先从**第 2.1 节**中推荐的声音中进行选择，按场景和说话者的**性别**进行过滤。
这些声音针对各自的专业用例（节奏、清晰度、语气）进行了专门优化。

**如果您的内容不属于这三个专业领域：**
→ 继续执行下面的步骤 2。

### 第 2 步：按性格特征选择（性别 + 年龄 + 语言）

对于非专业场景，根据以下三个性格特征，按照严格的优先顺序，从**第 2.2 节**中选择声音：

1. **性别**（最高优先级，不可协商）
   - 男性角色→**必须**使用男性声音
   - 女性角色→**必须**使用女性声音
   - 永远不要性别不匹配，即使其他特征看起来很合适

2. **年龄**（决定查看哪个小节）
   - **儿童** → 第 2.2 节“儿童的声音”
   - **青年**（青少年、年轻人）→ 第 2.2 节“青年之声”
   - **成人** → 第 2.2 节“成人声音”
   - **老年人** → 第 2.2 节“老年人的声音”

3. **语言**（必须与内容语言匹配）
   - 语音**必须**与正在生成的内容的语言相匹配
   - 中文内容→选择中文语音；韩语内容→选择韩语语音；英文内容→选择英文语音等
   - 如果第 2.2 节中不存在精确的语言匹配，则返回到目标语言的完整**系统语音列表**（第 3 节）

通过这三个特征缩小候选范围后，根据每个语音条目中描述的语音的**个性**、**语气**和**用例**选择最佳匹配。

### 快速参考决策流程```
Content Type?
├── Story/Narration/News/Documentary → Section 2.1 (filter by scenario + gender)
└── Other scenarios → Section 2.2:
    ├── 1. Match Gender (mandatory)
    ├── 2. Match Age Group (Children/Youth/Adult/Elderly/Professional)
    ├── 3. Match Language (must match content language)
    └── 4. Choose best fit by personality/tone
```---


## 2.语音推荐

### 2.1 按内容类型

**讲故事中的旁白和叙述者**
- 推荐：`audiobook_female_1`、`audiobook_male_1`
- 特点：适合讲故事、表演持续、清晰度清晰、节奏良好

**新闻与公告**
- 推荐：`中文（普通话）_新闻_主播`、`中文（普通话）_男_播音员`
- 特点：权威、清晰、专业节奏

**纪录片**
- 推荐：`doc_commentary`
- 特点：专业、清晰、节奏一致


### 2.2 按特征

#### 孩子们的声音

|语音 ID |名称 |描述 |最适合 |语言 |
|----------|------|-------------|---------|----------|
| `聪明男孩` | 男聪明童 |聪明、机智的男孩声音|儿童内容，教育性 |中文（普通话）|
| `可爱的男孩` | 可爱男童 |可爱的小男孩声音|儿童内容、动画 |中文（普通话）|
| `可爱的女孩` | 萌萌女童 |可爱甜美的女声|儿童故事、游戏|中文（普通话）|
|卡通猪 卡通猪小琪 |卡通人物声音|动画、喜剧、娱乐 |中文（普通话）|
| `韩国_SweetGirl` |甜美女孩|甜美可爱的少女声音|儿童内容、浪漫|韩语 |
| `印度尼西亚_SweetGirl` |甜美女孩|甜美可爱的女声|儿童内容，友善|印度尼西亚语 |
| `英语_甜_女孩` |甜美女孩|甜美天真的少女声音|儿童内容，友善|英语 |
| `西班牙_善良的女孩` |善良的女孩|温暖、富有同情心的女孩声音|儿童内容，温馨|西班牙语 |
| 《葡萄牙人_善良的女孩》|善良的女孩|温暖、富有同情心的女孩声音|儿童内容，温馨|葡萄牙语 |

####青春的声音

|语音 ID |名称 |描述 |最适合 |语言 |
|----------|------|-------------|---------|----------|
| `男qn情色` | 青涩青年 |青涩、缺乏经验的年轻人声音|校园故事、成长内容 |中文（普通话）|
| `男qn大学生` | 青年大学生 |年轻大学生心声|校园内容，教育 |中文（普通话）|
| `女少女` | 少女 |少女之声|浪漫、青春内容|中文（普通话）|
| `bingjiao_didi` | 病娇弟弟 |傲娇小弟声音|浪漫、人物驱动的内容 |中文（普通话）|
| `junlang_nanyou` | 俊朗男友 |帅气男友音|浪漫、约会内容 |中文（普通话）|
| `chunzhen_xuedi` | 纯真学弟 |天真烂漫的小学生声音|校园故事，青春内容|中文（普通话）|
| `lengdan_xiongzhang` | 冷淡学长 |酷学长声音|校园故事、浪漫|中文（普通话）|
| `diadia_xuemei` | 嗲嗲学妹 |轻浮的初中女孩声音|浪漫、约会内容 |中文（普通话）|
| `danya_xuejie` | 淡雅学姐 |优雅高级女声|校园故事、浪漫|中文（普通话）|
| `中文（普通话）_Straightforward_Boy` | 率真弟弟 |弗兰克、直率的男孩声音|休闲、直接的内容 |中文（普通话）|
| `中文（普通话）_真诚_成人` | 真诚青年|真诚的青年声音|诚实、真实的内容 |中文（普通话）|
| `中文（普通话）_纯心肠_男孩` | 清水邻家弟弟 |纯心邻居男孩的声音|纯真、有益健康的内容 |中文（普通话）|
| `韩国_开朗男友` |开朗的男朋友|充满活力、充满爱心的男友声音|浪漫、约会内容 |韩语 |
| `韩国_ShyGirl` |害羞的女孩|胆怯、矜持的女孩声音|喜剧、爱情 |韩语 |
| `日本_运动学生` |运动型学生|充满活力的运动学生声音|体育、青少年内容|日语 |
| `日本人_InnocentBoy` |天真无邪的男孩|纯真、天真的小男孩声音|儿童内容 |日语 |
| `Spanish_SincereTeen` |真诚青少年 |诚实、真实的青少年声音|青春，本真|西班牙语 |
| `西班牙_意志坚强的男孩` |意志坚强的男孩|坚定、执着的男孩声音|青春，动力|西班牙语 |

#### 成人的声音

|语音 ID |名称 |描述 |最适合 |语言 |
|----------|------|-------------|---------|----------|
| `女-成书` | 职业女性 |成熟女人的声音|复杂的成人内容 |中文（普通话）|
| `女宇杰` | 御姐 |成熟、优雅的女声|浪漫、专业的内容|中文（普通话）|
| `女天美` | 魅力女性 |甜美可人的女声|内容柔软、温和|中文（普通话）|
| `badao_shaoye` | 霸道少爷 |嚣张少爷声音|戏剧、角色|中文（普通话）|| `wumei_yujie` | 媚媚御姐 |迷人的成熟女人声音|浪漫、成熟的内容|中文（普通话）|
| `中文（普通话）_绅士` | 温润男声 |温柔儒雅的男声|旁白、讲故事 |中文（普通话）|
| `中文（普通话）_无拘无束的年轻人` | 不羁青年 |奔放的年轻人声音|休闲、娱乐内容 |中文（普通话）|
| `中文（普通话）_南方年轻人` | 南方小哥 |南方年轻人的声音|地域特色、休闲内容|中文（普通话）|
| `中文（普通话）_温柔_青春` | 温润青年 |温柔的年轻人声音|旁白，内容平静|中文（普通话）|
| `中文（普通话）_温暖_女孩` | 温暖少女 |温暖的少女声音|友好、支持性的内容 |中文（普通话）|
| `中文（普通话）_软妹` | 柔和温柔 |温柔的少女声音|平静、舒缓的内容 |中文（普通话）|
| `Korean_PlayboyCharmer` |花花公子魅力 |流畅、妖艳的男声|浪漫、娱乐|韩语 |
| `韩国_CalmLady` |冷静女士|沉稳、平静的女声|冥想、放松 |韩语 |
| `Spanish_ConfidentWoman` |自信的女人|自信干练的女人声音|专业，赋能 |西班牙语 |
| `葡萄牙_ConfidentWoman` |自信的女人|自信干练的女人声音|专业，赋能 |葡萄牙语 |

#### 老人的声音

|语音 ID |名称 |描述 |最适合 |语言 |
|----------|------|-------------|---------|----------|
| `中文（普通话）_幽默_长辈` | 搞笑大爷 |幽默的老人声音|喜剧、娱乐 |中文（普通话）|
| `中文（普通话）_善良_长辈` | 花甲奶奶 |慈祥老太太的声音|故事，内容温暖 |中文（普通话）|
| `中文（普通话）_善良_安蒂` | 热心大婶 |善良阿姨的声音|内容温暖、友善|中文（普通话）|
| `日本_知识分子前辈` |知识分子高级|睿智、知识渊博的长辈之声|解说，教育 |日语 |
| `韩国_知识分子高级` |知识分子高级|睿智、知识渊博的长辈之声|教育、解说 |韩语 |
| `Spanish_Wiselady` |聪明的女士|经验丰富、睿智的女人之声|指导、建议 |西班牙语 |
| `葡萄牙语_Wiselady` |聪明的女士|经验丰富、睿智的女人之声|指导、建议 |葡萄牙语 |
| `Spanish_SereneElder` |宁静长者|老人的声音平静、平和|冥想，智慧 |西班牙语 |
| `葡萄牙语_SereneElder` |宁静长者|老人的声音平静、平和|冥想，智慧 |葡萄牙语 |
| `英语_温柔的男人` |声音温柔的男人 |温柔的男声 | 温柔的男声 |平静、支持性的内容 |英语 |

---

## 系统语音列表（按语言分类）

### 中文普通话语音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `男qn情色` | 青涩青年 |青涩、缺乏经验的年轻人声音|校园故事、成长内容 |
| `男-qn-badao` | 霸道青年 |傲慢、霸道的年轻人声音|戏剧、爱情、角色 |
| `男qn大学生` | 青年大学生 |年轻大学生心声|校园内容，教育 |
| `女少女` | 少女 |少女之声|浪漫、青春内容|
| `女宇杰` | 御姐 |成熟、优雅的女声|浪漫、专业的内容|
| `女-成书` | 职业女性 |成熟女人的声音|复杂的成人内容 |
| `女天美` | 魅力女性 |甜美可人的女声|内容柔软、温和|
| `聪明男孩` | 男聪明童 |聪明、机智的男孩声音|儿童内容，教育性 |
| `可爱的男孩` | 可爱男童 |可爱的小男孩声音|儿童内容、动画 |
| `可爱的女孩` | 萌萌女童 |可爱甜美的女声|儿童故事、游戏|
|卡通猪 卡通猪小琪 |卡通人物声音|动画、喜剧、娱乐 |
| `bingjiao_didi` | 病娇弟弟 |傲娇小弟声音|浪漫、人物驱动的内容 |
| `junlang_nanyou` | 俊朗男友 |帅气男友音|浪漫、约会内容 |
| `chunzhen_xuedi` | 纯真学弟 |天真烂漫的小学生声音|校园故事，青春内容|
| `lengdan_xiongzhang` | 冷淡学长 |酷学长声音|校园故事、浪漫|
| `badao_shaoye` | 霸道少爷 |嚣张少爷声音|戏剧、角色|
| `tianxin_xiaoling` | 甜心小玲 |甜美的小灵声音|角色角色、动画 |
| `qiaopi_mengmei` | 俏皮萌妹 |俏皮可爱的女孩声音|喜剧、轻松的内容 |
| `wumei_yujie` | 媚媚御姐 |迷人的成熟女人声音|浪漫、成熟的内容|
| `diadia_xuemei` | 嗲嗲学妹 |轻浮的初中女孩声音|浪漫、约会内容 || `danya_xuejie` | 淡雅学姐 | Elegant senior girl voice | Campus stories, romance |
| `Arrogant_Miss` | 嚣张小姐 | Arrogant young lady voice | Drama, character roles |
| `Robot_Armor` | 机械战甲 | Robotic armor voice | Sci-fi, game characters |
| `Chinese (Mandarin)_Reliable_Executive` | 沉稳高管 | Reliable executive voice | Corporate, business content |
| `Chinese (Mandarin)_News_Anchor` | 新闻女声 | News anchor female voice | News broadcasts, current affairs |
| `Chinese (Mandarin)_Mature_Woman` | 傲娇御姐 | Tsundere mature woman voice | Romance, character-driven content |
| `Chinese (Mandarin)_Unrestrained_Young_Man` | 不羁青年 | Unrestrained young man voice | Casual, entertainment content |
| `male-qn-jingying` | 精英青年 | Elite, ambitious young man voice | Business, professional content |
| `Chinese (Mandarin)_Kind-hearted_Antie` | 热心大婶 | Kind-hearted auntie voice | Warm, friendly content |
| `Chinese (Mandarin)_HK_Flight_Attendant` | 港普空姐 | HK accent flight attendant voice | Regional character, entertainment |
| `Chinese (Mandarin)_Humorous_Elder` | 搞笑大爷 | Humorous old man voice | Comedy, entertainment |
| `Chinese (Mandarin)_Gentleman` | 温润男声 | Gentle, refined male voice | Narration, storytelling |
| `Chinese (Mandarin)_Warm_Bestie` | 温暖闺蜜 | Warm bestie female voice | Friendly, supportive content |
| `Chinese (Mandarin)_Male_Announcer` | 播报男声 | Male announcer voice | Announcements, broadcasts |
| `Chinese (Mandarin)_Sweet_Lady` | 甜美女声 | Sweet lady voice | Soft, gentle content |
| `Chinese (Mandarin)_Southern_Young_Man` | 南方小哥 | Southern young man voice | Regional character, casual content |
| `Chinese (Mandarin)_Wise_Women` | 阅历姐姐 | Experienced wise woman voice | Advice, guidance content |
| `Chinese (Mandarin)_Gentle_Youth` | 温润青年 | Gentle young man voice | Narration, calm content |
| `Chinese (Mandarin)_Warm_Girl` | 温暖少女 | Warm young girl voice | Friendly, supportive content |
| `Chinese (Mandarin)_Kind-hearted_Elder` | 花甲奶奶 | Kind elderly lady voice | Stories, warm content |
| `Chinese (Mandarin)_Cute_Spirit` | 憨憨萌兽 | Cute cartoon spirit voice | Animations, children's content |
| `Chinese (Mandarin)_Radio_Host` | 电台男主播 | Radio host male voice | Podcasts, radio shows |
| `Chinese (Mandarin)_Lyrical_Voice` | 抒情男声 ​​| Lyrical male singing voice | Music, singing content |
| `Chinese (Mandarin)_Straightforward_Boy` | 率真弟弟 | Frank, straightforward boy voice | Casual, direct content |
| `Chinese (Mandarin)_Sincere_Adult` | 真诚青年 | Sincere young adult voice | Honest, genuine content |
| `Chinese (Mandarin)_Gentle_Senior` | 温柔学姐 | Gentle senior girl voice | Campus stories, supportive content |
| `Chinese (Mandarin)_Stubborn_Friend` | 嘴硬竹马 | Stubborn childhood friend voice | Drama, character-driven content |
| `Chinese (Mandarin)_Crisp_Girl` | 清脆少女 | Crisp, clear young girl voice | Clear, bright content |
| `Chinese (Mandarin)_Pure-hearted_Boy` | 清澈邻家弟弟 | Pure-hearted neighbor boy voice | Innocent, wholesome content |
| `Chinese (Mandarin)_Soft_Girl` | 柔和少女 | Soft, gentle girl voice | Calm, soothing content |

### Chinese Cantonese Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Cantonese_ProfessionalHost（F)` | 专业女主持 | Professional female host voice | Cantonese broadcasts, hosting |
| `Cantonese_GentleLady` | 温柔女声 | Gentle Cantonese female voice | Soft, warm Cantonese content |
| `Cantonese_ProfessionalHost（M)` | 专业男主持 | Professional male host voice | Cantonese broadcasts, hosting |
| `Cantonese_PlayfulMan` | 活泼男声 | Playful Cantonese male voice | Entertainment, casual content |
| `Cantonese_CuteGirl` | 可爱女孩 | Cute Cantonese girl voice | Children's content, animations |
| `Cantonese_KindWoman` | 善良女声 | Kind Cantonese female voice | Warm, friendly content |

### English Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Santa_Claus` | Santa Claus | Festive, jolly male voice | Holiday content, children's stories |
| `Grinch` | Grinch | Whiny, mischievous voice | Comedy, entertainment, holiday |
| `Rudolph` | Rudolph | Cute, nasal reindeer voice | Children's content, holiday |
| `Arnold` | Arnold | Deep, robotic terminator voice | Sci-fi, action, character roles |
| `Charming_Santa` | Charming Santa | Smooth, charismatic Santa voice | Holiday, entertainment |
| `Charming_Lady` | Charming Lady | Elegant, sophisticated female voice | Professional, romance |
| `Sweet_Girl` | Sweet Girl | Sweet, innocent young girl voice | Children's content, friendly || `可爱的小精灵` |可爱的小精灵|俏皮的小精灵声音|奇幻、儿童内容 |
| `有吸引力的女孩` |有魅力的女孩 |迷人、迷人的女声|娱乐、营销|
| `宁静的女人` |宁静的女人|平静、平和的女声|冥想、放松 |
| `English_Trustworthy_Man` |值得信赖的人|可靠、真诚的男声 |商业、旁白|
| `English_Graceful_Lady` |优雅女士|优雅脱俗的女声|正式、专业|
| `英国人澳大利亚人` |澳洲帅哥 |休闲、友善的澳大利亚男声 |休闲、娱乐|
| `English_Whispering_girl` |耳语女孩|轻柔的、耳语般的声音 |浪漫、亲密的内容 |
| `英语_勤奋_男人` |勤奋的人|勤奋认真的男声 |励志、教育 |
| `英语_温柔的男人` |声音温柔的男人 |温柔的男声 | 温柔的男声 |平静、支持性的内容 |

### 日语配音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `日本_知识分子前辈` |知识分子高级|睿智、知识渊博的长辈之声|解说，教育 |
| 《日本果断公主》 |果断公主|自信、皇家公主的声音|动画、游戏、戏剧|
| `日本_LoyalKnight` |忠诚骑士 |勇敢、忠诚的骑士之声|奇幻、游戏、故事 |
| `日本_DominantMan` |主导男人|雄浑有力、威严的男声|行动、领导力|
| `日本_严肃指挥官` |严肃的指挥官|严厉、权威的指挥官声音|军事、游戏|
| `日本_ColdQueen` |冷酷女王 |遥远、威严的女王声音|剧情、奇幻 |
| `日本_可靠的女人` |可靠的女人|可靠、支持性的女性声音 |支持、指导 |
| `日本人_温柔管家` |温柔管家|礼貌、儒雅的仆人声音|喜剧、动画 |
| `日本人_KindLady` |善良的女士|温暖、温柔的贵妇声音|温暖、安慰|
| `日本_CalmLady` |冷静女士|沉稳、平静的女声|冥想、放松 |
| 《日本乐观青年》 |乐观青年|开朗、积极的年轻人声音|青春内容、动力|
| `日本人_慷慨的居酒屋老板` |慷慨的居酒屋老板|友好、热情的酒馆老板的声音|休闲、喜剧 |
| `日本_运动学生` |运动型学生|充满活力的运动学生声音|体育、青少年内容|
| `日本人_InnocentBoy` |天真无邪的男孩|纯真、天真的小男孩声音|儿童内容 |
| `日本_GracefulMaiden` |优雅少女|优雅、温柔的少妇声音|浪漫、戏剧 |

### 韩国声音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `韩国_SweetGirl` |甜美女孩|甜美可爱的少女声音|儿童内容、浪漫|
| `韩国_开朗男友` |开朗的男朋友|充满活力、充满爱心的男友声音|浪漫、约会内容 |
| `韩国_迷人妹妹` |妖娆姐姐|迷人迷人的姐姐声音|家庭、戏剧 |
| `韩国_ShyGirl` |害羞的女孩|胆怯、矜持的女孩声音|喜剧、爱情 |
| `韩国_可靠姐姐` |可靠姐姐|值得信赖、可靠的姐姐声音|支持、指导 |
| `Korean_StrictBoss` |严格的老板|权威、苛求的老板声音|商业、戏剧 |
| `韩国_野蛮女孩` |野蛮女孩 |大胆、机智的女孩声音|喜剧、娱乐 |
| `韩国_ChildhoodFriendGirl` |儿时朋友女孩|熟悉、友善的儿时好友声音|浪漫、怀旧|
| `Korean_PlayboyCharmer` |花花公子魅力 |流畅、妖艳的男声|浪漫、娱乐|
| `韩国_优雅公主` |优雅公主|优雅、皇家的公主声音|动画、奇幻 |
| `韩国_勇敢女战士` |勇敢的女战士|勇敢的女战士声音|动作、奇幻 |
| 《韩国勇敢青年》 |勇敢的青春|英雄少年之声|行动，青春|
| `韩国_CalmLady` |冷静女士|沉稳、平静的女声|冥想、放松 |
| `韩国_EnthusiasticTeen` |热情青少年 |兴奋、充满活力的少年声音|青春内容|
| `韩国_SoothingLady` |舒缓女士|平静、安慰的女声|放松，支持|
| `韩国_知识分子高级` |知识分子高级|睿智、知识渊博的长辈之声|教育、解说 |
| `韩国_LonelyWarrior` |孤独的战士|孤独、忧郁的战士声音|剧情、奇幻 |
| '韩国_成熟女士' |成熟女士 |成熟的成年女性声音|专业、戏剧|| `Korean_InnocentBoy` |天真无邪的男孩|纯真、天真的小男孩声音|儿童内容 |
| `韩国_魅力姐姐` |迷人姐姐|迷人、悦耳的姐姐声音|家庭、浪漫 |
| `Korean_AthleticStudent` |运动学生|运动、充满活力的学生声音 |运动、青少年|
| `韩国_勇敢冒险家` |勇敢的冒险家 |勇敢的探险家之声|冒险、奇幻|
| `韩国_冷静绅士` |冷静的绅士|沉稳、优雅的绅士声音 |正式、专业|
| `Korean_WiseElf` |聪明的精灵|古老、神秘的精灵声音|奇幻、旁白 |
| `Korean_CheerfulCoolJunior` |开朗酷少年|流行、友好的初级声音 |青春、娱乐|
| `韩国_果断女王` |果断女王|权威、指挥女王声音 |剧情、奇幻 |
| `Korean_ColdYoungMan` |冷酷的年轻人|遥远而冷漠的年轻人声音|剧情、爱情 |
| `韩国_神秘女孩` |神秘女孩|神秘、神秘的女孩声音|悬疑、剧情 |
| `韩国_QuirkyGirl` |古怪的女孩|古怪而独特的女声|喜剧、娱乐 |
| `Korean_ConsiderateSenior` |体贴的前辈 |体贴、关爱的长辈声音|温暖、支持|
| `韩国_开朗小妹妹` |性格开朗的小妹妹|俏皮可爱的妹妹声音|家庭、喜剧 |
| `Korean_DominantMan` |主导男人|雄浑有力、威严的男声|领导力、行动 |
| `韩国_空头女孩` |傻女孩 |活泼、空旷的女孩声音|喜剧、娱乐 |
| `韩国_可靠青年` |可靠的青年|值得信赖、可靠的年轻人声音 |支持，青年|
| `韩国_友好大姐姐` |友善的大姐姐|温暖、有保护欲的姐姐声音|家人，支持|
| `韩国_GentleBoss` |温柔的老板|亲切、善解人意的老板声音|商业，支持|
| `韩国_冷女孩` |冷酷女孩|孤傲疏远的女声|剧情、爱情 |
| `韩国_傲慢女士` |傲慢的女士 |傲慢、骄傲的女人声音|戏剧、喜剧 |
| `韩国_迷人姐姐` |迷人姐姐|迷人、优雅的姐姐声音 |浪漫、家庭|
| `韩国_知识分子` |知识分子|聪明、知识渊博的男声|教育、专业 |
| `韩国_CaringWoman` |关爱女人|培养、支持女性的声音|支持、温暖|
| `韩国_WiseTeacher` |智慧老师|经验丰富、知识渊博的老师之声|教育 |
| `韩国_ConfidentBoss` |自信的老板|自信、干练的老板心声|商业、领导力 |
| `Korean_AthleticGirl` |运动女孩|运动、充满活力的女孩声音|运动、健身|
| `韩国_占有欲男人` |占有欲强的男人 |强烈、保护性的男声 |浪漫、戏剧 |
| `韩国_GentleWoman` |温柔的女人|温柔的女人声音|温柔的女人声音|冷静、支持 |
| `Korean_CockyGuy` |自大的家伙|自信又略带傲慢的男声|喜剧、娱乐 |
| `韩国_体贴的女人` |体贴的女人|深思熟虑、充满关怀的女人声音|剧情，支持|
| 《韩国乐观青年》 |乐观青年|积极、充满希望的年轻人声音|动力，青春|

### 西班牙语之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `Spanish_SereneWoman` |宁静的女人|平静、平和的女声|放松、冥想|
| `Spanish_MaturePartner` |成熟的合作伙伴|成熟的成人伴侣声音 |浪漫、戏剧 |
| `西班牙语_迷人的故事讲述者` |迷人的讲故事者 |引人入胜、富有磁性的叙述者声音 |有声读物、讲故事|
| `西班牙语_旁白` |旁白|专业叙事声音|纪录片、旁白 |
| `Spanish_WiseScholar` |智者学者|知识渊博、睿智学者的声音|教育、历史 |
| `西班牙_善良的女孩` |善良的女孩|温暖、富有同情心的女孩声音|儿童内容，温馨|
| `Spanish_DeterminedManager` |坚定的经理|雄心勃勃、干劲十足的经理之声|商业，动力|
| `Spanish_BossyLeader` |专横的领袖 |指挥、权威的领袖声音|领导力、戏剧 |
| `Spanish_ReservedYoungMan` |矜持的年轻人|安静、内向的年轻人声音|戏剧，现实人物|
| `Spanish_ConfidentWoman` |自信的女人|自信干练的女人声音|专业，赋能 |
| `Spanish_ThoughtfulMan` |体贴的人|反思、聪明的男人声音|教育、戏剧 |
| `西班牙_意志坚强的男孩` |意志坚强的男孩|坚定、执着的男孩声音|青春，动力|| `Spanish_SophisticatedLady` |精致女士 |优雅精致的女声|正式、浪漫 |
| `Spanish_RationalMan` |理性人|逻辑性强、善于分析的男人声音 |教育、商业 |
| `Spanish_AnimeCharacter` |动漫人物 |夸张的动漫风格声音|动画、娱乐|
| `Spanish_Deep-tonedMan` |深色调的男人 |低沉、洪亮的男声|魅力十足、威风凛凛|
| `西班牙_挑剔的女主人` |挑剔的女主人|女主人声音特别挑剔|喜剧、正剧 |
| `Spanish_SincereTeen` |真诚青少年 |诚实、真实的青少年声音|青春，本真|
| `Spanish_FrankLady` |弗兰克夫人|直接、诚实的女人声音|喜剧、正剧 |
| `西班牙喜剧演员` |喜剧演员 |幽默风趣的声音|喜剧、娱乐 |
| `西班牙语_辩手` |辩手 |议论性、有说服力的声音|辩论、讨论|
| `Spanish_ToughBoss` |严厉的老板|严厉、要求严格的老板声音|商业、戏剧 |
| `Spanish_Wiselady` |聪明的女士|经验丰富、睿智的女人之声|指导、建议 |
| `Spanish_Steadymentor` |稳定的导师|可靠、支持性的导师声音 |教育、指导 |
| `Spanish_Jovialman` |快活的人 |开朗、友善的男人声音|休闲娱乐|
| `西班牙语_圣诞老人` |圣诞老人|节日圣诞老人的声音|假期，孩子们|
| `西班牙语_鲁道夫` |鲁道夫|驯鹿的声音 |假期，孩子们|
| `Spanish_Intonategirl` |语调女孩|音乐、旋律优美的女孩声音|音乐、歌唱|
| `西班牙语_阿诺德` |阿诺德|机器人、机械声音|科幻、动作 |
| `西班牙幽灵` |幽灵|阴森、空灵的声音|恐怖、神秘 |
| `Spanish_HumorousElder` |幽默长辈|有趣的老人声音|喜剧、娱乐 |
| `Spanish_EnergeticBoy` |精力充沛的男孩|活跃、活泼的男孩声音|青少年、运动|
| `Spanish_WhimsicalGirl` |异想天开的女孩 |俏皮、富有想象力的女孩声音 |儿童、奇幻 |
| `Spanish_StrictBoss` |严格的老板|严厉、要求严格的老板心声|商业、教育|
| `Spanish_ReliableMan` |可靠的人|值得信赖、可靠的男人声音|专业，支持|
| `Spanish_SereneElder` |宁静长者|老人的声音平静、平和|冥想，智慧 |
| `Spanish_AngryMan` |愤怒的人|沮丧、恼怒的男声 |戏剧、喜剧 |
| `Spanish_AssertiveQueen` |自信的女王 |自信、威严的女王声音|剧情、奇幻 |
| `Spanish_CaringGirlfriend` |贴心女友|培养、关爱女友的声音|浪漫、关系 |
| `西班牙_强大的士兵` |强大的士兵|坚强、勇敢的士兵之声|军事行动 |
| `Spanish_PassionateWarrior` |热血战士|凶猛、专注的战士声音|动作、奇幻 |
| `Spanish_ChattyGirl` |健谈的女孩 |健谈、善于交际的女孩声音 |喜剧、社交 |
| `西班牙_浪漫丈夫` |浪漫的丈夫|充满爱、浪漫的老公声音|浪漫、家庭|
| `Spanish_CompellingGirl` |迷人的女孩 |有说服力、磁性的女孩声音|营销、娱乐|
| `Spanish_PowerfulVeteran` |实力老将|经验丰富、实力雄厚的老兵声音|军事、戏剧|
| `Spanish_SensibleManager` |明智的经理 |实用、合理的经理心声|商务、指导|
| `Spanish_ThoughtfulLady` |体贴的女士|体贴、亲切的女士声音|支持，建议|

### 葡萄牙语声音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `葡萄牙_感伤女士` |感伤女士|情绪化、敏感的女士声音|剧情、爱情 |
| `葡萄牙_BossyLeader` |专横的领袖 |指挥、权威的领袖声音|领导力、戏剧 |
| `葡萄牙语_Wiselady` |聪明的女士|经验丰富、睿智的女人之声|指导、建议 |
| `葡萄牙人_意志坚强的男孩` |意志坚强的男孩|坚定、执着的男孩声音|青春，动力|
| `葡萄牙语_深沉的绅士` |声音低沉的绅士|低沉浑厚的男声|魅力十足、威风凛凛|
| `葡萄牙_UpsetGirl` |心烦意乱的女孩|心疼、情绪化的女孩声音 |戏剧、现实|
| `葡萄牙_热情战士` |热血战士|凶猛、专注的战士声音|动作、奇幻 |
| `葡萄牙语_动漫角色` |动漫人物 |夸张的动漫风格声音|动画、娱乐|
| `葡萄牙_ConfidentWoman` |自信的女人|自信干练的女人声音|专业，赋能 |
| `葡萄牙语_AngryMan` |愤怒的人|沮丧、恼怒的男声 |戏剧、喜剧 || `葡萄牙语_迷人的故事讲述者` |迷人的讲故事者 |引人入胜、富有磁性的叙述者声音 |有声读物、讲故事|
| 《葡萄牙语教父》 |教父|权威、有力的父亲形象声音|剧情强大|
| `葡萄牙人_保留年轻人` |矜持的年轻人|安静、内向的年轻人声音|戏剧、现实|
| `葡萄牙语_SmartYoungGirl` |聪明的年轻女孩|聪明、乖巧的女孩声音|教育、青少年 |
| 《葡萄牙人_善良的女孩》|善良的女孩|温暖、富有同情心的女孩声音|儿童内容，温馨|
| `葡萄牙_Pompouslady` |浮夸的女士|自以为是、傲慢的女士声音|喜剧、正剧 |
| `葡萄牙格林奇` |格林奇 |发牢骚、调皮的声音 |喜剧、娱乐 |
| `葡萄牙辩手` |辩手 |议论性、有说服力的声音|辩论、讨论|
| `葡萄牙_SweetGirl` |甜美女孩|甜美可爱的女声|儿童内容、浪漫|
| `葡萄牙_AttractiveGirl` |有魅力的女孩 |迷人、吸引人的女声|娱乐、浪漫|
| `葡萄牙人_体贴的人` |体贴的人|反思、聪明的男人声音|教育、戏剧 |
| `葡萄牙_PlayfulGirl` |顽皮的女孩|俏皮、爱玩的女声|喜剧、儿童内容 |
| `葡萄牙_GorgeousLady` |华丽女士|美丽迷人的女士声音|浪漫、娱乐|
| `葡萄牙语_LovelyLady` |可爱的女士|甜美可爱的女士声音|热情、友善|
| `葡萄牙语_SereneWoman` |宁静的女人|平静、平和的女声|放松、冥想|
| `葡萄牙语_SadTeen` |悲伤的青少年|忧郁的少年声音|戏剧、情感 |
| `葡萄牙_成熟伴侣` |成熟的合作伙伴|成熟的成人伴侣声音 |浪漫、戏剧 |
| `葡萄牙喜剧演员` |喜剧演员 |幽默风趣的声音|喜剧、娱乐 |
| `葡萄牙语_NaughtySchoolgirl` |顽皮的女学生|调皮、顽皮的学生声音|喜剧、学校 |
| `葡萄牙语_旁白` |旁白|专业叙事声音|纪录片、旁白 |
| `葡萄牙_ToughBoss` |严厉的老板|严厉、要求严格的老板声音|商业、戏剧 |
| `葡萄牙_挑剔的女主人` |挑剔的女主人|女主人声音特别挑剔|喜剧、正剧 |
| `葡萄牙戏剧家` |戏剧家 |戏剧性、富有表现力的声音 |戏剧、讲故事 |
| `葡萄牙语_Steadymentor` |稳定的导师|可靠、支持性的导师声音 |教育、指导 |
| `葡萄牙语_Jovialman` |快活的人 |开朗、友善的男人声音|休闲娱乐|
| `葡萄牙魅力女王` |迷人女王|优雅迷人的女王声音|剧情、奇幻 |
| `葡萄牙_圣诞老人` |圣诞老人|节日圣诞老人的声音|假期，孩子们|
| `葡萄牙鲁道夫` |鲁道夫|驯鹿的声音 |假期，孩子们|
| `葡萄牙语_阿诺德` |阿诺德|机器人、机械声音|科幻、动作 |
| `葡萄牙_迷人圣诞老人` |迷人的圣诞老人 |流畅、富有魅力的圣诞老人声音 |度假、娱乐|
| `葡萄牙_CharmingLady` |迷人女士|优雅精致的女士声音 |专业、浪漫|
| `葡萄牙_幽灵` |幽灵|阴森、空灵的声音|恐怖、神秘 |
| `葡萄牙语_幽默长者` |幽默长辈|有趣的老人声音|喜剧、娱乐 |
| `葡萄牙_CalmLeader` |冷静领袖 |沉着、稳定的领导者声音 |领导、指导 |
| `葡萄牙语_温柔老师` |温柔的老师|和蔼、耐心的老师声音|教育性、支持性|
| `葡萄牙_EnergeticBoy` |精力充沛的男孩|活跃、活泼的男孩声音|青少年、运动|
| `葡萄牙_ReliableMan` |可靠的人|值得信赖、可靠的男人声音|专业，支持|
| `葡萄牙语_SereneElder` |宁静长者|老人的声音平静、平和|冥想，智慧 |
| `葡萄牙语_GrimReaper` |死神|阴暗、不祥的声音|恐怖、奇幻|
| `葡萄牙_AssertiveQueen` |自信的女王 |自信、威严的女王声音|剧情、奇幻 |
| `葡萄牙_异想天开的女孩` |异想天开的女孩 |俏皮、富有想象力的女孩声音 |儿童、奇幻 |
| `葡萄牙_StressedLady` |压力大的女士|女士的声音焦急、不知所措|喜剧、现实 |
| `葡萄牙语_友好邻居` |友好邻邦|热情、乐于助人的邻居之声 |社区、家庭|
| `葡萄牙语_贴心女朋友` |贴心女友|培养、关爱女友的声音|浪漫、关系 |
| `葡萄牙_强大的士兵` |强大的士兵|坚强、勇敢的士兵之声|军事行动 || `葡萄牙_FascinatingBoy` |迷人的男孩|迷人、有趣的男孩声音|浪漫、青春|
| `葡萄牙人_浪漫丈夫` |浪漫的丈夫|充满爱、浪漫的老公声音|浪漫、家庭|
| `葡萄牙_StrictBoss` |严格的老板|严厉、要求严格的老板心声|商业、教育|
| `葡萄牙_鼓舞人心的女士` |鼓舞人心的女士|励志、鼓励的女士声音|动机、领导力|
| `葡萄牙语_PlayfulSpirit` |俏皮精神|开朗、调皮的精灵声音|奇幻，儿童 |
| `葡萄牙_ElegantGirl` |优雅女孩|优雅脱俗的女声|正式、浪漫 |
| `Portuguese_CompellingGirl` |迷人的女孩 |有说服力、磁性的女孩声音|营销、娱乐|
| `葡萄牙人_强大的退伍军人` |实力老将|经验丰富、实力雄厚的老兵声音|军事、戏剧|
| `葡萄牙_SensibleManager` |明智的经理 |实用、合理的经理心声|商务、指导|
| `葡萄牙_体贴的女士` |体贴的女士|体贴、亲切的女士声音|支持，建议|
| `葡萄牙戏剧演员` |戏剧演员 |戏剧性、富有表现力的演员声音|戏剧、娱乐 |
| `葡萄牙_FragileBoy` |脆弱的男孩|敏感、脆弱的男孩声音|戏剧、情感 |
| `葡萄牙语_ChattyGirl` |健谈的女孩 |健谈、善于交际的女孩声音 |喜剧、社交 |
| `葡萄牙语_认真的教练` |认真的导师|细心、勤奋的教练声音|教育、培训|
| `葡萄牙语_RationalMan` |理性人|逻辑性强、善于分析的男人声音 |教育、商业 |
| `葡萄牙_WiseScholar` |智者学者|知识渊博、睿智学者的声音|教育、历史 |
| `葡萄牙语_FrankLady` |弗兰克夫人|直接、诚实的女人声音|喜剧、正剧 |
| `Portuguese_DeterminedManager` |坚定的经理|雄心勃勃、干劲十足的经理之声|商业，动力|

### 法语之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `法语_男性_语音_新` |头脑冷静的人 |冷静、理智的男声|专业、解说 |
| `法国女新闻主播` |耐心的女主持人 |清晰、耐心的新闻主持人声音 |新闻、广播 |
| `French_CasualMan` |休闲男士 |轻松、随意的男声|休闲、娱乐|
| `French_MovieLeadFemale` |电影女主角 |戏剧性、富有表现力的女声|戏剧、娱乐 |
| `French_FemaleAnchor` |女主播|专业女主播声音|新闻、广播 |

### 印尼语声音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `印度尼西亚_SweetGirl` |甜美女孩|甜美可爱的女声|儿童内容，友善|
| `Indonesian_ReservedYoungMan` |矜持的年轻人|安静、内向的年轻人声音|戏剧、现实|
| `印度尼西亚_CharmingGirl` |迷人的女孩|迷人、吸引人的女孩声音|娱乐、浪漫|
| `印度尼西亚_CalmWoman` |冷静的女人|沉稳、平和的女声 |放松、冥想|
| `Indonesian_ConfidentWoman` |自信的女人|自信干练的女人声音|专业，赋能 |
| `印度尼西亚_CaringMan` |贴心人|培养、支持男人的声音|家人支持 |
| `Indonesian_BossyLeader` |专横的领袖 |指挥、权威的领袖声音|领导力、戏剧 |
| `印度尼西亚_DeterminedBoy` |坚定的男孩|雄心勃勃、执着的男孩声音|青春，动力|
| `印度尼西亚_GentleGirl` |温柔的女孩|温柔的女孩声音 | 温柔的女孩声音冷静、支持 |

### 德国之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `German_FriendlyMan` |友善的人|温暖平易近人的男声|休闲、友善 |
| `German_SweetLady` |甜美女士|悦耳、亲切的女士声音|温暖、支持|
| `德国_PlayfulMan` |顽皮的男人|风趣幽默的男声|喜剧、娱乐 |

### 俄罗斯之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `Russian_HandsomeChildhoodFriend` |帅气儿时好友|迷人的儿时声音|浪漫、怀旧|
| `Russian_BrightHeroine` |光明女王 |活泼有力的女主声音|剧情、动作 |
| `Russian_AmbitiousWoman` |雄心勃勃的女人|充满干劲、坚定的女人声音|专业、激励|
| `Russian_ReliableMan` |可靠的人|值得信赖、可靠的男人声音|专业，支持|| `Russian_CrazyQueen` |疯狂女孩|狂野、难以捉摸的女声|喜剧、正剧 |
| `Russian_PessimisticGirl` |悲观的女孩|阴沉、消极的女孩声音|喜剧、正剧 |
| `Russian_AttractiveGuy` |有魅力的家伙 |迷人、吸引人的男声|浪漫、娱乐|
| `俄罗斯_脾气暴躁的男孩` |脾气暴躁的男孩|烦躁、脾气暴躁的男孩声音|喜剧、正剧 |

### 意大利之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `Italian_BraveHeroine` |勇敢的女主角|勇敢、英雄的女声 |动作、奇幻 |
| `意大利语_旁白` |旁白|专业叙事声音|纪录片、讲故事 |
| `Italian_WanderingSorcerer` |流浪法师|神秘、旅行的魔术师声音|奇幻、冒险|
| `Italian_DiligentLeader` |勤奋的领导者|勤劳、敬业的领导者之声|领导力，商业|

### 阿拉伯语声音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `Arabic_CalmWoman` |冷静的女人|沉稳、平和的女声 |放松、冥想|
| `Arabic_FriendlyGuy` |友善的家伙|温暖平易近人的男声|休闲、友善 |

### 土耳其语声音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `土耳其_CalmWoman` |冷静的女人|沉稳、平和的女声 |放松、冥想|
| `土耳其_值得信赖的人` |值得信赖的人|可靠、真诚的男声 |专业、商务|

### 乌克兰之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `乌克兰_CalmWoman` |冷静的女人|沉稳、平和的女声 |放松、冥想|
| `乌克兰_WiseScholar` |智者学者|知识渊博、睿智学者的声音|教育、历史 |

### 荷兰之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `荷兰人善良的女孩` |善良的女孩|温暖、富有同情心的女孩声音|儿童内容，温馨|
| `Dutch_bossy_leader` |专横的领导者 |指挥、权威的领袖声音|领导力、戏剧 |

### 越南声音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `越南_kindheard_girl` |善良的女孩|温暖、富有同情心的女孩声音|儿童内容，温馨|

### 泰语之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `Thai_male_1_sample8` |平静的人 |冷静平和的男声|放松、冥想|
| `Thai_male_2_sample2` |友善的人|温暖平易近人的男声|休闲、友善 |
| `Thai_female_1_sample1` |自信的女人|自信干练的女人声音|专业，赋能 |
| `Thai_female_2_sample2` |充满活力的女人|活跃、活泼的女声 |动力、能量 |

### 波兰之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `Polish_male_1_sample4` |男旁白|专业叙事声音|纪录片、旁白 |
| `Polish_male_2_sample3` |男主播|专业男主播声音|新闻、广播 |
| `Polish_female_1_sample1` |冷静的女人|沉稳、平和的女声 |放松、冥想|
| `Polish_female_2_sample3` |休闲女人|轻松、随意的女声 |休闲、娱乐|

### 罗马尼亚语声音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `Romanian_male_1_sample2` |可靠的人|值得信赖、可靠的男人声音|专业，支持|
| `Romanian_male_2_sample1` |活力青年 |活跃、活泼的年轻人声音|青春，动力|
| `Romanian_female_1_sample4` |乐观青年|积极、充满希望的年轻人声音|动力，青春|
| `Romanian_female_2_sample1` |温柔的女人|温柔的女人声音|温柔的女人声音|冷静、支持 |

### 希腊之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `greek_male_1a_v1` |贴心导师|深思熟虑、睿智的导师之声 |教育、指导 |
| `Greek_female_1_sample1` |温柔女士|说话轻柔、亲切的女士声音|冷静、支持 |
| `Greek_female_2_sample3` |邻家女孩 |友善平易近人的女孩声音|休闲、友善 |

### 捷克之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|| `czech_male_1_v1` |放心的演讲者 |自信、专业的演讲者声音 |演示、广播 |
| `czech_female_5_v7` |坚定的叙述者|可靠、一致的叙述者声音 |纪录片、讲故事 |
| `czech_female_2_v2` |优雅女士|优雅精致的女士声音|正式、专业|

### 芬兰之声

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `finnish_male_3_v1` |乐观的男人|开朗、充满活力的男声 |激励、娱乐 |
| `finnish_male_1_v2` |友善的男孩|温暖、平易近人的男孩声音|儿童内容，友善|
| `finnish_female_4_v1` |自信的女人|自信、有力的女声|专业，赋能 |

### 印地语声音

|语音 ID |名称 |描述 |最适合 |
|----------|------|-------------|----------|
| `hindi_male_1_v2` |值得信赖的顾问|可靠、明智的顾问之声 |指导、建议 |
| `hindi_female_2_v1` |宁静的女人|平静、平和的女声|放松、冥想|
| `hindi_female_1_v2` |新闻主播 |专业新闻主播声音|新闻、广播 |

---

## 语音参数

### VoiceSetting 数据类```python
from utils import VoiceSetting

voice = VoiceSetting(
    voice_id="male-qn-qingse",  # Required: Voice ID
    speed=1.0,                   # Optional: 0.5 (slower) to 2.0 (faster), default 1.0
    volume=1.0,                  # Optional: 0.1 (quieter) to 10.0 (louder), default 1.0
    pitch=0,                     # Optional: -12 (deeper) to 12 (higher), default 0
    emotion="calm",           # Optional: happy, sad, angry, fearful, disgusted, surprised, calm, fluent, whisper
)
```### 参数指南

**速度**
- 0.75：较慢、刻意的讲话（新闻、教程）
- 1.0：正常节奏（大部分内容）
- 1.25：稍快（充满活力的内容）
- 1.5+：快节奏（时间敏感的内容）

**体积**
- 0.8-1.0：正常听力水平
- 1.0-1.5：声音更大以吸引注意力
- < 0.8：更柔和、亲密的感觉

**推介**
- -6到-3：更深入、更权威
- 0：自然音调
- +3 至 +6：更高、更有活力

**情感**
- ‘平静’：平静、中性的语气
- ‘流利’：流利、自然的语气
- `whisper`：轻声细语，柔和的语气
- `happy`：开朗、乐观的语气
- `sad`：忧郁、忧郁的语气
- ‘愤怒’：沮丧、激烈的语气
- ‘害怕’：焦虑、紧张的语气
- `disgusted`: 排斥、反感的语气
- ‘惊讶’：惊讶、惊讶的语气


## 自定义声音

### 语音克隆

从音频样本创建自定义声音，以获得独特的品牌声音。

**要求：**
- 源音频：10秒到5分钟
- 格式：mp3、wav、m4a
- 大小：最大 20MB
- 质量：清晰，无背景噪音，单扬声器

**最佳实践：**
- 使用 30-60 秒干净的言语
- 包括不同的语调和情感
- 在安静的环境中录制
- 始终保持一致的音量

### 声音设计

通过创意项目的文字描述产生新的声音。

**何时使用：**
- 现有的声音不符合您的需求
- 需要独特的角色声音
- 全语音克隆之前的原型

**提示指南：**
- 包括：性别、年龄、声音特征、情绪基调、用例
- 明确节奏、语气和目标受众
- 示例：“温暖、祖母般的声音，节奏轻柔，非常适合睡前故事”