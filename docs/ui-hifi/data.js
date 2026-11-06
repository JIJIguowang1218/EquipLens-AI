/* 自动生成，勿手改：python scripts/build_hifi_data.py
   来源：data-test/ui-fixtures/*.json（模拟数据） */
window.HIFI = {
 "s1": {
  "fixture": "s1-retrieval",
  "version": "1.0",
  "generated_at": "2026-11-05",
  "notice": "模拟数据：用于高保真填充与联调，数值与文案按真实链路的结构生成，不代表真实检索结果。生成脚本 scripts/make_ui_fixtures.py",
  "contract": "docs/ui-fixture-spec.md",
  "prose_ref": "docs/ui-interaction-spec-v3.md §9",
  "request": {
   "raw": "沙漠牵引车，看踏步和防护栏，六台",
   "category": "沙漠牵引车",
   "parts": [
    "踏步",
    "防护栏"
   ],
   "want": 6
  },
  "analysis": {
   "axes": [
    "exact",
    "environment",
    "platform",
    "cross_vehicle"
   ],
   "prose": "沙漠牵引车以 6×6 为基型，前脸、格栅与保险杠属平台通用造型件，不随工况变化。沙漠工况的特化落在防护栏、进气防护、底盘离地与踏步防滑上，这些部件即使未被点名，亦构成本类车型的设计特征。前脸与驾驶室轮廓承自基型平台，同平台车型可验证其家族关系。踏步、爬梯与把手为功能件，构型跨车型可比，证据强度弱，仅作备选。"
  },
  "budget": {
   "recommended": 6,
   "backup": 2,
   "requested": 12
  },
  "cards": [
   {
    "id": "t01",
    "role": "recommended",
    "model": "德龙X3000",
    "configuration": "德龙X3000 6x6",
    "relation": "exact",
    "tier": 1,
    "confidence": 0.8,
    "selected": true,
    "reason": "6x6 沙漠越野构型，三件部件可裁；证据见 evidence（E3：标题含型号的详情/专文页）",
    "evidence": [
     {
      "title": "惊现陕汽德龙X3000 6x6沙漠越野车 这个展会的“硬菜”真不少！",
      "url": "https://baijiahao.baidu.com/s?id=1570689637613090",
      "grade": "E3"
     },
     {
      "title": "【陕汽重卡 德龙X3000 375马力 6X6 国五沙漠越野载货车底盘】参数|对比_卡车网",
      "url": "https://www.chinatruck.org/product/truck/21165_36_1.html",
      "grade": "E3"
     }
    ],
    "images": [
     "../../data-test/ab-images/03-陕汽重卡-德龙X3000-6X6-沙漠越野载货车/1.jpg",
     "../../data-test/ab-images/03-陕汽重卡-德龙X3000-6X6-沙漠越野载货车/2.jpg",
     "../../data-test/ab-images/03-陕汽重卡-德龙X3000-6X6-沙漠越野载货车/3.jpg",
     "../../data-test/ab-images/03-陕汽重卡-德龙X3000-6X6-沙漠越野载货车/4.jpg"
    ],
    "image_count": 4,
    "image_state": "ok",
    "brand": "陕汽",
    "config": "6×6",
    "label": "6×6 · 陕汽"
   },
   {
    "id": "t02",
    "role": "recommended",
    "model": "德龙F3000",
    "configuration": "德龙F3000",
    "relation": "exact",
    "tier": 1,
    "confidence": 0.8,
    "selected": true,
    "reason": "上代沙漠车，看图解级文本与底盘构型；证据见 evidence（E3：标题含型号的详情/专文页）",
    "evidence": [
     {
      "title": "_陕汽重卡德龙F3000 外观 评测 设计_ - 精选笔记",
      "url": "https://www.baidu.com/s?pd=note&rpf=pc&word=%E9%99%95%E6%B1%BD%E9%87%8D%E5%8D%A1%E5%BE%B7%E9%BE%99F3000+%E5%A4%96%E8%A7%82+%E8%AF%84%E6%B5%8B+%E8%AE%BE%E8%AE%A1&sa=vs_video_top_ugc",
      "grade": "E3"
     },
     {
      "title": "_陕汽重卡德龙F3000 造型 设计语言_ - 批发厂家 - 百度爱采购",
      "url": "https://b2b.baidu.com/cc?q=%E9%99%95%E6%B1%BD%E9%87%8D%E5%8D%A1%E5%BE%B7%E9%BE%99F3000%20%E9%80%A0%E5%9E%8B%20%E8%AE%BE%E8%AE%A1%E8%AF%AD%E8%A8%80&from=b2b_factory2&srcid=5359&from_restype=&pi=baidu.b2b_factory2.title...a4e71ddb00088099",
      "grade": "E3"
     }
    ],
    "images": [
     "../../data-test/ab-images/11-陕汽重卡-德龙F3000/1.jpg",
     "../../data-test/ab-images/11-陕汽重卡-德龙F3000/2.jpg",
     "../../data-test/ab-images/11-陕汽重卡-德龙F3000/3.jpg",
     "../../data-test/ab-images/11-陕汽重卡-德龙F3000/4.jpg"
    ],
    "image_count": 4,
    "image_state": "ok",
    "brand": "陕汽",
    "config": "",
    "label": "陕汽"
   },
   {
    "id": "t03",
    "role": "recommended",
    "model": "H6066",
    "configuration": "H6066 6x6",
    "relation": "exact",
    "tier": 1,
    "confidence": 0.8,
    "selected": true,
    "reason": "塔里木油田沙漠孤鹰，特种运输构型；证据见 evidence（E3：标题含型号的详情/专文页）",
    "evidence": [
     {
      "title": "塔里木油田里的沙漠孤鹰，H6066 6x6特种运输车了解一下",
      "url": "https://m.360che.com/market/200615/149004.html",
      "grade": "E3"
     }
    ],
    "images": [
     "../../data-test/ab-images/14-H6066-6x6/1.jpg",
     "../../data-test/ab-images/14-H6066-6x6/2.jpg",
     "../../data-test/ab-images/14-H6066-6x6/3.jpg",
     "../../data-test/ab-images/14-H6066-6x6/4.jpg"
    ],
    "image_count": 4,
    "image_state": "ok",
    "brand": "陕汽",
    "config": "6×6",
    "label": "6×6 · 陕汽"
   },
   {
    "id": "t04",
    "role": "recommended",
    "model": "豪沃",
    "configuration": "豪沃 6x6",
    "relation": "exact",
    "tier": 1,
    "confidence": 0.8,
    "selected": true,
    "reason": "HOWO 6x6 油田牵引车，图解证据多；证据见 evidence（E3：标题含型号的详情/专文页）",
    "evidence": [
     {
      "title": "酷似尼古拉斯！豪沃6X6油田牵引车图解_手机卡车之家",
      "url": "https://m.360che.com/tech/160303/52370.html",
      "grade": "E3"
     },
     {
      "title": "酷似尼古拉新！HOWO 6X6油田牵引车图解",
      "url": "https://www.yunshuren.com/article-3419.html",
      "grade": "E3"
     }
    ],
    "images": [
     "../../data-test/ab-images/15-豪沃-6x6/1.jpg",
     "../../data-test/ab-images/15-豪沃-6x6/2.jpg",
     "../../data-test/ab-images/15-豪沃-6x6/3.jpg"
    ],
    "image_count": 3,
    "image_state": "ok",
    "brand": "重汽",
    "config": "6×6",
    "label": "6×6 · 重汽"
   },
   {
    "id": "t07",
    "role": "recommended",
    "model": "中国重汽",
    "configuration": "HOWO",
    "relation": "environment",
    "tier": 2,
    "confidence": 0.6,
    "selected": true,
    "reason": "HOWO 平台驾驶室与踏板构型，作基型对照；证据见 evidence",
    "evidence": [
     {
      "title": "物流驰骋新选择 中国重汽HOWO悍将25款轻卡：科技加持 品质跃升-新浪汽车",
      "url": "http://k.sina.com.cn/article_3786353850_e1af2cba00101re0g.html",
      "grade": "E3"
     },
     {
      "title": "原创丨34.99万元！中国重汽HOWO MAX高性价比无敌|max|重卡|howo_网易订阅",
      "url": "https://www.163.com/dy/article/GLSV3QJD05520UDK.html",
      "grade": "E3"
     }
    ],
    "images": [
     "../../data-test/ab-images/12-中国重汽-HOWO-MAX/1.jpg",
     "../../data-test/ab-images/12-中国重汽-HOWO-MAX/2.jpg",
     "../../data-test/ab-images/12-中国重汽-HOWO-MAX/3.jpg",
     "../../data-test/ab-images/12-中国重汽-HOWO-MAX/4.jpg"
    ],
    "image_count": 4,
    "image_state": "ok",
    "brand": "重汽",
    "config": "",
    "label": "重汽"
   },
   {
    "id": "t08",
    "role": "recommended",
    "model": "解放",
    "configuration": "解放 CA2191P2K2T 6x6",
    "relation": "environment",
    "tier": 2,
    "confidence": 0.6,
    "selected": true,
    "reason": "6x6 越野汽车，军用底子；证据见 evidence（E3：标题含型号的详情/专文页）",
    "evidence": [
     {
      "title": "解放 CA2191P2K2T 6×6平头柴油越野汽车",
      "url": "https://www.17vin.com/gonggao/45173/CA2191P2K2T.html",
      "grade": "E3"
     }
    ],
    "images": [
     "../../data-test/ab-images/18-解放-CA2191P2K2T-6x6/1.jpg",
     "../../data-test/ab-images/18-解放-CA2191P2K2T-6x6/2.jpg",
     "../../data-test/ab-images/18-解放-CA2191P2K2T-6x6/3.jpg",
     "../../data-test/ab-images/18-解放-CA2191P2K2T-6x6/4.jpg"
    ],
    "image_count": 4,
    "image_state": "ok",
    "brand": "一汽",
    "config": "6×6",
    "label": "6×6 · 一汽"
   },
   {
    "id": "t09",
    "role": "backup",
    "model": "德龙新M3000",
    "configuration": "德龙新M3000",
    "relation": "platform",
    "tier": 3,
    "confidence": 0.35,
    "selected": false,
    "reason": "驾驶室平台对照；6x6 变体未核，弱关联；证据见 evidence（E3：标题含型号的详情/专文页）",
    "evidence": [
     {
      "title": "德龙新M3000和HOWO TH7参数对比-易车",
      "url": "https://car.yiche.com/canshuduibi/7049-7023.html",
      "grade": "E3"
     }
    ],
    "images": [
     "../../data-test/ab-images/21-德龙新M3000/1.jpg",
     "../../data-test/ab-images/21-德龙新M3000/2.jpg",
     "../../data-test/ab-images/21-德龙新M3000/3.jpg",
     "../../data-test/ab-images/21-德龙新M3000/4.jpg"
    ],
    "image_count": 4,
    "image_state": "ok",
    "brand": "陕汽",
    "config": "",
    "label": "陕汽"
   },
   {
    "id": "t12",
    "role": "backup",
    "model": "解放",
    "configuration": "JH6",
    "relation": "platform",
    "tier": 3,
    "confidence": 0.35,
    "selected": false,
    "reason": "JH6 驾驶室平台对照；与沙漠主线关联弱，需构型核验",
    "evidence": [
     {
      "title": "一汽解放JH6 _重卡_ 全解析:多少钱?什么配置?和J6P比哪个好?",
      "url": "http://www.baidu.com/link?url=k-cg9SlBzdK6kBeye2biNd9tqQ4NjPzk0t3NIORPwelyVBOmCQWkPsasW7yOvXUuvrcv31ku8f-CgaoyQ6uocYT5MZkMexFda7fJ7e5X4gpRWX_nb4D3ROTt6BQ0_LuHf2ucpLxYnpxuhuAAhidMbiX3FpsiQd96RlyYCyPj7GAoJwoWBPotT-0VGLIMnCUUoT6iZwA_VlqNzkhCuS1aVLGgTWJNMQ0hODwB_4TzUYBoTnjlzkJ8qKnVNSuex0ZD",
      "grade": "E3"
     },
     {
      "title": "_一汽解放JH6 外观 评测 设计_ - 精选笔记",
      "url": "https://www.baidu.com/s?pd=note&rpf=pc&word=%E4%B8%80%E6%B1%BD%E8%A7%A3%E6%94%BEJH6+%E5%A4%96%E8%A7%82+%E8%AF%84%E6%B5%8B+%E8%AE%BE%E8%AE%A1&sa=vs_video_top_ugc",
      "grade": "E3"
     }
    ],
    "images": [
     "../../data-test/ab-images/10-一汽解放-JH6/1.jpg",
     "../../data-test/ab-images/10-一汽解放-JH6/2.jpg",
     "../../data-test/ab-images/10-一汽解放-JH6/3.jpg",
     "../../data-test/ab-images/10-一汽解放-JH6/4.jpg"
    ],
    "image_count": 4,
    "image_state": "ok",
    "brand": "一汽",
    "config": "",
    "label": "一汽"
   }
  ]
 },
 "s2": {
  "fixture": "s2-analysis",
  "version": "1.0",
  "generated_at": "2026-11-05",
  "notice": "模拟数据：用于高保真填充与联调，数值与文案按真实链路的结构生成，不代表真实检索结果。生成脚本 scripts/make_ui_fixtures.py",
  "contract": "docs/ui-fixture-spec.md",
  "schema_ref": "docs/superpowers/specs/2026-10-31-analysis-schema-design.md",
  "slots": [
   "grille",
   "bumper",
   "side_guard",
   "wheel_arch",
   "step"
  ],
  "slot_labels": {
   "grille": "进气格栅",
   "bumper": "保险杠",
   "side_guard": "侧防护栏",
   "wheel_arch": "翼子板与轮拱",
   "step": "登车踏步"
  },
  "vehicles": [
   {
    "id": "v1",
    "name": "德龙 X3000",
    "brand": "陕汽",
    "configuration": "6×6 沙漠越野",
    "style_tags": [
     {
      "tag": "敦实",
      "cluster": "stability",
      "evidence": "横向饰条贯通至灯缘"
     },
     {
      "tag": "硬朗",
      "cluster": "tough",
      "evidence": "格栅直边与方形灯腔"
     },
     {
      "tag": "整面化",
      "cluster": "modern",
      "evidence": "保险杠与面罩同色连片"
     }
    ],
    "views": [
     {
      "id": "v1-m1",
      "view": "hero_lf",
      "image": "../../data-test/ab-images/03-陕汽重卡-德龙X3000-6X6-沙漠越野载货车/1.jpg",
      "analysis": {
       "unit": {
        "slot": "front_face",
        "kind": "region",
        "members": [
         "grille",
         "bumper"
        ],
        "gesture": "前脸竖直上收，面幅横向铺开。",
        "character_lines": [
         "横向饰条自格栅贯通至大灯上缘。",
         "格栅竖线止于保险杠上沿。",
         "腰线自车门平直延至车尾。"
        ],
        "proportion": "前脸接近 2:1 扁宽，驾驶室高宽比偏方（估）。",
        "cmf": "车身同色漆，格栅与保险杠下段哑黑。",
        "judgement": "横向分层压住车头体量。",
        "style_tags": [
         {
          "tag": "敦实",
          "cluster": "stability",
          "evidence": "横向饰条贯通至灯缘"
         },
         {
          "tag": "硬朗",
          "cluster": "tough",
          "evidence": "格栅直边与方形灯腔"
         },
         {
          "tag": "整面化",
          "cluster": "modern",
          "evidence": "保险杠与面罩同色连片"
         }
        ]
       },
       "parts": [
        {
         "slot": "grille",
         "label": "grille",
         "term": "横置多层格栅",
         "aliases": [
          "多横幅格栅"
         ],
         "part_family": "sheet_metal",
         "family_reason": "三层板条连续排布",
         "visible": "full",
         "bbox": [
          70,
          420,
          180,
          550
         ],
         "form": [
          "三层横向饰条贯通车头，止于大灯内缘。",
          "两端收进灯腔，宽度略窄于前脸。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "哑黑喷涂"
         },
         "intent": "横向拉宽车头视觉，压低头部重心。"
        },
        {
         "slot": "bumper",
         "label": "bumper",
         "term": "整体式保险杠",
         "aliases": [
          "一体式前包围"
         ],
         "part_family": "sheet_metal",
         "family_reason": "单一连续件无横向分缝",
         "visible": "full",
         "bbox": [
          20,
          600,
          220,
          710
         ],
         "form": [
          "单一连续件包住车头下部，无横向分缝。",
          "下沿内收，两端留出雾灯位。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "同色漆"
         },
         "intent": "减少接缝积砂，便于冲洗。"
        },
        {
         "slot": "side_guard",
         "label": "side_guard",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "wheel_arch",
         "label": "wheel_arch",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "step",
         "label": "step",
         "term": "两级固定踏板",
         "aliases": [
          "两级踏步"
         ],
         "part_family": "function_attachment",
         "family_reason": "独立踏板挂装于车门下沿",
         "visible": "full",
         "bbox": [
          200,
          630,
          310,
          800
         ],
         "form": [
          "两级踏板上下错开，层间留可见空隙。",
          "踏面压防滑齿纹，最下层悬空。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "防滑涂层"
         },
         "intent": "两级降低登车高度，悬空层避免托底。"
        }
       ],
       "unplaced": []
      }
     },
     {
      "id": "v1-m2",
      "view": "side_l",
      "image": "../../data-test/ab-images/03-陕汽重卡-德龙X3000-6X6-沙漠越野载货车/2.jpg",
      "analysis": {
       "unit": {
        "slot": "front_face",
        "kind": "region",
        "members": [
         "grille",
         "bumper"
        ],
        "gesture": "前脸竖直上收，面幅横向铺开。",
        "character_lines": [
         "横向饰条自格栅贯通至大灯上缘。",
         "格栅竖线止于保险杠上沿。",
         "腰线自车门平直延至车尾。"
        ],
        "proportion": "前脸接近 2:1 扁宽，驾驶室高宽比偏方（估）。",
        "cmf": "车身同色漆，格栅与保险杠下段哑黑。",
        "judgement": "横向分层压住车头体量。",
        "style_tags": [
         {
          "tag": "敦实",
          "cluster": "stability",
          "evidence": "横向饰条贯通至灯缘"
         },
         {
          "tag": "硬朗",
          "cluster": "tough",
          "evidence": "格栅直边与方形灯腔"
         },
         {
          "tag": "整面化",
          "cluster": "modern",
          "evidence": "保险杠与面罩同色连片"
         }
        ]
       },
       "parts": [
        {
         "slot": "grille",
         "label": "grille",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "bumper",
         "label": "bumper",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "side_guard",
         "label": "side_guard",
         "term": "型钢侧防护栏",
         "aliases": [
          "方钢护栏"
         ],
         "part_family": "frame_profile",
         "family_reason": "方管主体加竖支腿",
         "visible": "full",
         "bbox": [
          310,
          620,
          600,
          760
         ],
         "form": [
          "方管横贯前后轮之间，三根竖支腿连车架。",
          "端部与轮拱留出装配间隙。"
         ],
         "cmf": {
          "material_class": "钢制型材",
          "finish": "防锈漆"
         },
         "intent": "防对向车辆卷入，兼作侧向支撑。"
        },
        {
         "slot": "wheel_arch",
         "label": "wheel_arch",
         "term": "方形轮拱",
         "aliases": [],
         "part_family": "sheet_metal",
         "family_reason": "拱缘直边折角包住轮胎",
         "visible": "full",
         "bbox": [
          560,
          600,
          700,
          880
         ],
         "form": [
          "拱缘带直边折角，外扩包住轮胎上半。",
          "后端与踏步护板相接，形成侧向折线。"
         ],
         "cmf": {
          "material_class": "塑料",
          "finish": "黑色未喷漆"
         },
         "intent": "折角抬升离地感，兼挡飞石。"
        },
        {
         "slot": "step",
         "label": "step",
         "term": "两级固定踏板",
         "aliases": [
          "两级踏步"
         ],
         "part_family": "function_attachment",
         "family_reason": "独立踏板挂装于车门下沿",
         "visible": "full",
         "bbox": [
          200,
          640,
          320,
          820
         ],
         "form": [
          "两级踏板上下错开，层间留可见空隙。",
          "踏面压防滑齿纹，最下层悬空。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "防滑涂层"
         },
         "intent": "两级降低登车高度，悬空层避免托底。"
        }
       ],
       "unplaced": []
      }
     },
     {
      "id": "v1-m3",
      "view": "front",
      "image": "../../data-test/ab-images/03-陕汽重卡-德龙X3000-6X6-沙漠越野载货车/3.jpg",
      "analysis": {
       "unit": {
        "slot": "front_face",
        "kind": "region",
        "members": [
         "grille",
         "bumper"
        ],
        "gesture": "前脸竖直上收，面幅横向铺开。",
        "character_lines": [
         "横向饰条自格栅贯通至大灯上缘。",
         "格栅竖线止于保险杠上沿。",
         "腰线自车门平直延至车尾。"
        ],
        "proportion": "前脸接近 2:1 扁宽，驾驶室高宽比偏方（估）。",
        "cmf": "车身同色漆，格栅与保险杠下段哑黑。",
        "judgement": "横向分层压住车头体量。",
        "style_tags": [
         {
          "tag": "敦实",
          "cluster": "stability",
          "evidence": "横向饰条贯通至灯缘"
         },
         {
          "tag": "硬朗",
          "cluster": "tough",
          "evidence": "格栅直边与方形灯腔"
         },
         {
          "tag": "整面化",
          "cluster": "modern",
          "evidence": "保险杠与面罩同色连片"
         }
        ]
       },
       "parts": [
        {
         "slot": "grille",
         "label": "grille",
         "term": "横置多层格栅",
         "aliases": [
          "多横幅格栅"
         ],
         "part_family": "sheet_metal",
         "family_reason": "三层板条连续排布",
         "visible": "full",
         "bbox": [
          80,
          400,
          210,
          560
         ],
         "form": [
          "三层横向饰条贯通车头，止于大灯内缘。",
          "两端收进灯腔，宽度略窄于前脸。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "哑黑喷涂"
         },
         "intent": "横向拉宽车头视觉，压低头部重心。"
        },
        {
         "slot": "bumper",
         "label": "bumper",
         "term": "整体式保险杠",
         "aliases": [
          "一体式前包围"
         ],
         "part_family": "sheet_metal",
         "family_reason": "单一连续件无横向分缝",
         "visible": "full",
         "bbox": [
          30,
          590,
          240,
          720
         ],
         "form": [
          "单一连续件包住车头下部，无横向分缝。",
          "下沿内收，两端留出雾灯位。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "同色漆"
         },
         "intent": "减少接缝积砂，便于冲洗。"
        },
        {
         "slot": "side_guard",
         "label": "side_guard",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "wheel_arch",
         "label": "wheel_arch",
         "term": "方形轮拱",
         "aliases": [],
         "part_family": "sheet_metal",
         "family_reason": "拱缘直边折角包住轮胎",
         "visible": "full",
         "bbox": [
          600,
          620,
          720,
          870
         ],
         "form": [
          "拱缘带直边折角，外扩包住轮胎上半。",
          "后端与踏步护板相接，形成侧向折线。"
         ],
         "cmf": {
          "material_class": "塑料",
          "finish": "黑色未喷漆"
         },
         "intent": "折角抬升离地感，兼挡飞石。"
        },
        {
         "slot": "step",
         "label": "step",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        }
       ],
       "unplaced": []
      }
     }
    ]
   },
   {
    "id": "v2",
    "name": "豪沃 TX7",
    "brand": "重汽",
    "configuration": "6×6 牵引",
    "style_tags": [
     {
      "tag": "稳重",
      "cluster": "stability",
      "evidence": "网板外框横向完整"
     },
     {
      "tag": "刚直",
      "cluster": "tough",
      "evidence": "灯腔转角接近直角"
     },
     {
      "tag": "参数化",
      "cluster": "modern",
      "evidence": "孔阵横向等距排布"
     }
    ],
    "views": [
     {
      "id": "v2-m1",
      "view": "hero_lf",
      "image": "../../data-test/ab-images/15-豪沃-6x6/1.jpg",
      "analysis": {
       "unit": {
        "slot": "front_face",
        "kind": "region",
        "members": [
         "grille",
         "bumper"
        ],
        "gesture": "前脸整片网板，转折压在下沿。",
        "character_lines": [
         "网板外框宽出灯组外缘。",
         "下沿折线自保险杠上沿横贯两端。",
         "A 柱前倾，与顶盖连成一道弧。"
        ],
        "proportion": "网板宽高比约 1.6:1，占前脸三分之二（估）。",
        "cmf": "面罩哑黑，车身同色漆，踏步黑漆。",
        "judgement": "大面积网板压低视觉重心。",
        "style_tags": [
         {
          "tag": "稳重",
          "cluster": "stability",
          "evidence": "网板外框横向完整"
         },
         {
          "tag": "刚直",
          "cluster": "tough",
          "evidence": "灯腔转角接近直角"
         },
         {
          "tag": "参数化",
          "cluster": "modern",
          "evidence": "孔阵横向等距排布"
         }
        ]
       },
       "parts": [
        {
         "slot": "grille",
         "label": "grille",
         "term": "冲孔网板格栅",
         "aliases": [
          "冲孔面板"
         ],
         "part_family": "sheet_metal",
         "family_reason": "整片网板一次冲孔",
         "visible": "full",
         "bbox": [
          60,
          400,
          200,
          570
         ],
         "form": [
          "整片网板占满前脸中部，外框厚约一指。",
          "孔径沿横向等距排布。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "哑黑喷塑"
         },
         "intent": "整片网板遮住散热器，减少积沙。"
        },
        {
         "slot": "bumper",
         "label": "bumper",
         "term": "分体式保险杠",
         "aliases": [
          "上下分体"
         ],
         "part_family": "sheet_metal",
         "family_reason": "上下两段可见分缝",
         "visible": "full",
         "bbox": [
          20,
          590,
          230,
          720
         ],
         "form": [
          "上下两段以一道分缝隔开，上段同色。",
          "下段独立，两端包住雾灯。"
         ],
         "cmf": {
          "material_class": "塑料",
          "finish": "同色漆与哑黑"
         },
         "intent": "下段可单独更换，降低维修成本。"
        },
        {
         "slot": "side_guard",
         "label": "side_guard",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "wheel_arch",
         "label": "wheel_arch",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "step",
         "label": "step",
         "term": "单级固定踏板",
         "aliases": [
          "一级踏板"
         ],
         "part_family": "function_attachment",
         "family_reason": "单级踏板挂装于车门下沿",
         "visible": "full",
         "bbox": [
          190,
          640,
          300,
          810
         ],
         "form": [
          "单级踏板挂装于车门下沿，踏面外伸。",
          "下方以两根支架连车架。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "防滑涂层"
         },
         "intent": "单级降低登车高度，结构简单。"
        }
       ],
       "unplaced": []
      }
     },
     {
      "id": "v2-m2",
      "view": "side_l",
      "image": "../../data-test/ab-images/15-豪沃-6x6/2.jpg",
      "analysis": {
       "unit": {
        "slot": "front_face",
        "kind": "region",
        "members": [
         "grille",
         "bumper"
        ],
        "gesture": "前脸整片网板，转折压在下沿。",
        "character_lines": [
         "网板外框宽出灯组外缘。",
         "下沿折线自保险杠上沿横贯两端。",
         "A 柱前倾，与顶盖连成一道弧。"
        ],
        "proportion": "网板宽高比约 1.6:1，占前脸三分之二（估）。",
        "cmf": "面罩哑黑，车身同色漆，踏步黑漆。",
        "judgement": "大面积网板压低视觉重心。",
        "style_tags": [
         {
          "tag": "稳重",
          "cluster": "stability",
          "evidence": "网板外框横向完整"
         },
         {
          "tag": "刚直",
          "cluster": "tough",
          "evidence": "灯腔转角接近直角"
         },
         {
          "tag": "参数化",
          "cluster": "modern",
          "evidence": "孔阵横向等距排布"
         }
        ]
       },
       "parts": [
        {
         "slot": "grille",
         "label": "grille",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "bumper",
         "label": "bumper",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "side_guard",
         "label": "side_guard",
         "term": "管式侧防护栏",
         "aliases": [
          "圆管护栏"
         ],
         "part_family": "frame_profile",
         "family_reason": "圆管主体加竖支腿",
         "visible": "full",
         "bbox": [
          300,
          630,
          590,
          770
         ],
         "form": [
          "圆管主体横贯前后轮之间，两端收进车架。",
          "三根竖支腿垂直落地。"
         ],
         "cmf": {
          "material_class": "钢管",
          "finish": "防锈漆"
         },
         "intent": "圆管受力均匀，减少对向车卷入。"
        },
        {
         "slot": "wheel_arch",
         "label": "wheel_arch",
         "term": "分体式轮眉",
         "aliases": [
          "外挂轮眉"
         ],
         "part_family": "sheet_metal",
         "family_reason": "黑色包边外挂于翼子板",
         "visible": "full",
         "bbox": [
          550,
          600,
          690,
          870
         ],
         "form": [
          "黑色包边外挂于翼子板，高出钣金面。",
          "后端沿车门下沿收回。"
         ],
         "cmf": {
          "material_class": "塑料",
          "finish": "黑色未喷漆"
         },
         "intent": "外挂轮眉挡住飞石，减少钣金损伤。"
        },
        {
         "slot": "step",
         "label": "step",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        }
       ],
       "unplaced": []
      }
     },
     {
      "id": "v2-m3",
      "view": "front",
      "image": "../../data-test/ab-images/15-豪沃-6x6/3.jpg",
      "analysis": {
       "unit": {
        "slot": "front_face",
        "kind": "region",
        "members": [
         "grille",
         "bumper"
        ],
        "gesture": "前脸整片网板，转折压在下沿。",
        "character_lines": [
         "网板外框宽出灯组外缘。",
         "下沿折线自保险杠上沿横贯两端。",
         "A 柱前倾，与顶盖连成一道弧。"
        ],
        "proportion": "网板宽高比约 1.6:1，占前脸三分之二（估）。",
        "cmf": "面罩哑黑，车身同色漆，踏步黑漆。",
        "judgement": "大面积网板压低视觉重心。",
        "style_tags": [
         {
          "tag": "稳重",
          "cluster": "stability",
          "evidence": "网板外框横向完整"
         },
         {
          "tag": "刚直",
          "cluster": "tough",
          "evidence": "灯腔转角接近直角"
         },
         {
          "tag": "参数化",
          "cluster": "modern",
          "evidence": "孔阵横向等距排布"
         }
        ]
       },
       "parts": [
        {
         "slot": "grille",
         "label": "grille",
         "term": "冲孔网板格栅",
         "aliases": [
          "冲孔面板"
         ],
         "part_family": "sheet_metal",
         "family_reason": "整片网板一次冲孔",
         "visible": "full",
         "bbox": [
          70,
          390,
          220,
          580
         ],
         "form": [
          "整片网板占满前脸中部，外框厚约一指。",
          "孔径沿横向等距排布。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "哑黑喷塑"
         },
         "intent": "整片网板遮住散热器，减少积沙。"
        },
        {
         "slot": "bumper",
         "label": "bumper",
         "term": "分体式保险杠",
         "aliases": [
          "上下分体"
         ],
         "part_family": "sheet_metal",
         "family_reason": "上下两段可见分缝",
         "visible": "full",
         "bbox": [
          30,
          580,
          250,
          730
         ],
         "form": [
          "上下两段以一道分缝隔开，上段同色。",
          "下段独立，两端包住雾灯。"
         ],
         "cmf": {
          "material_class": "塑料",
          "finish": "同色漆与哑黑"
         },
         "intent": "下段可单独更换，降低维修成本。"
        },
        {
         "slot": "side_guard",
         "label": "side_guard",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "wheel_arch",
         "label": "wheel_arch",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "step",
         "label": "step",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        }
       ],
       "unplaced": []
      }
     }
    ]
   },
   {
    "id": "v3",
    "name": "解放 JH6",
    "brand": "一汽",
    "configuration": "6×4 牵引",
    "style_tags": [
     {
      "tag": "扎实",
      "cluster": "stability",
      "evidence": "保险杠下沿通长平直"
     },
     {
      "tag": "方峻",
      "cluster": "tough",
      "evidence": "灯腔与面罩成直角"
     },
     {
      "tag": "规整",
      "cluster": "precision",
      "evidence": "饰条等距平行"
     }
    ],
    "views": [
     {
      "id": "v3-m1",
      "view": "hero_lf",
      "image": "../../data-test/ab-images/10-一汽解放-JH6/1.jpg",
      "analysis": {
       "unit": {
        "slot": "front_face",
        "kind": "region",
        "members": [
         "grille",
         "bumper"
        ],
        "gesture": "前脸上收，转角落在灯腔外沿。",
        "character_lines": [
         "双横饰条压在格栅上三分之一。",
         "保险杠下沿平直，两端不外抛。",
         "侧窗下沿与腰线平行。"
        ],
        "proportion": "前脸接近 1.8:1，驾驶室偏高窄（估）。",
        "cmf": "车身同色漆，格栅镀铬，轮拱同色。",
        "judgement": "平直折线让前脸显干练。",
        "style_tags": [
         {
          "tag": "扎实",
          "cluster": "stability",
          "evidence": "保险杠下沿通长平直"
         },
         {
          "tag": "方峻",
          "cluster": "tough",
          "evidence": "灯腔与面罩成直角"
         },
         {
          "tag": "规整",
          "cluster": "precision",
          "evidence": "饰条等距平行"
         }
        ]
       },
       "parts": [
        {
         "slot": "grille",
         "label": "grille",
         "term": "横置多层格栅",
         "aliases": [
          "多横幅格栅"
         ],
         "part_family": "sheet_metal",
         "family_reason": "两层横向板条",
         "visible": "full",
         "bbox": [
          70,
          410,
          190,
          560
         ],
         "form": [
          "两道横向饰条压在上三分之一，镀铬包边。",
          "板条间距一致，止于灯腔内缘。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "镀铬与哑黑"
         },
         "intent": "横向饰条拉宽前脸，镀铬提亮上沿。"
        },
        {
         "slot": "bumper",
         "label": "bumper",
         "term": "整体式保险杠",
         "aliases": [
          "一体式前包围"
         ],
         "part_family": "sheet_metal",
         "family_reason": "单一连续件",
         "visible": "full",
         "bbox": [
          20,
          600,
          220,
          720
         ],
         "form": [
          "单一连续件包住车头下部，下沿通长平直。",
          "两端不外抛，与轮眉齐平。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "同色漆"
         },
         "intent": "平直下沿保持离地间隙，便于判断接近角。"
        },
        {
         "slot": "side_guard",
         "label": "side_guard",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "wheel_arch",
         "label": "wheel_arch",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "step",
         "label": "step",
         "term": "两级固定踏板",
         "aliases": [
          "两级踏步"
         ],
         "part_family": "function_attachment",
         "family_reason": "两级踏板挂装",
         "visible": "full",
         "bbox": [
          200,
          640,
          310,
          800
         ],
         "form": [
          "两级踏板错开布置，层间留缝。",
          "踏面外缘与车门下沿齐平。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "防滑涂层"
         },
         "intent": "两级降低登车高度，齐平外缘减少风阻。"
        }
       ],
       "unplaced": []
      }
     },
     {
      "id": "v3-m2",
      "view": "side_l",
      "image": "../../data-test/ab-images/10-一汽解放-JH6/2.jpg",
      "analysis": {
       "unit": {
        "slot": "front_face",
        "kind": "region",
        "members": [
         "grille",
         "bumper"
        ],
        "gesture": "前脸上收，转角落在灯腔外沿。",
        "character_lines": [
         "双横饰条压在格栅上三分之一。",
         "保险杠下沿平直，两端不外抛。",
         "侧窗下沿与腰线平行。"
        ],
        "proportion": "前脸接近 1.8:1，驾驶室偏高窄（估）。",
        "cmf": "车身同色漆，格栅镀铬，轮拱同色。",
        "judgement": "平直折线让前脸显干练。",
        "style_tags": [
         {
          "tag": "扎实",
          "cluster": "stability",
          "evidence": "保险杠下沿通长平直"
         },
         {
          "tag": "方峻",
          "cluster": "tough",
          "evidence": "灯腔与面罩成直角"
         },
         {
          "tag": "规整",
          "cluster": "precision",
          "evidence": "饰条等距平行"
         }
        ]
       },
       "parts": [
        {
         "slot": "grille",
         "label": "grille",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "bumper",
         "label": "bumper",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "side_guard",
         "label": "side_guard",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "wheel_arch",
         "label": "wheel_arch",
         "term": "一体式同色轮拱",
         "aliases": [
          "齐平轮眉"
         ],
         "part_family": "sheet_metal",
         "family_reason": "与车身同色同曲面",
         "visible": "full",
         "bbox": [
          560,
          610,
          700,
          880
         ],
         "form": [
          "轮拱与车身同色同曲面，无独立包边。",
          "拱缘一道浅折线收进翼子板。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "同色漆"
         },
         "intent": "同色轮拱弱化轮眉，保持侧面整面。"
        },
        {
         "slot": "step",
         "label": "step",
         "term": "两级固定踏板",
         "aliases": [
          "两级踏步"
         ],
         "part_family": "function_attachment",
         "family_reason": "两级踏板挂装",
         "visible": "full",
         "bbox": [
          200,
          650,
          320,
          820
         ],
         "form": [
          "两级踏板错开布置，层间留缝。",
          "踏面外缘与车门下沿齐平。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "防滑涂层"
         },
         "intent": "两级降低登车高度，齐平外缘减少风阻。"
        }
       ],
       "unplaced": []
      }
     },
     {
      "id": "v3-m3",
      "view": "front",
      "image": "../../data-test/ab-images/10-一汽解放-JH6/3.jpg",
      "analysis": {
       "unit": {
        "slot": "front_face",
        "kind": "region",
        "members": [
         "grille",
         "bumper"
        ],
        "gesture": "前脸上收，转角落在灯腔外沿。",
        "character_lines": [
         "双横饰条压在格栅上三分之一。",
         "保险杠下沿平直，两端不外抛。",
         "侧窗下沿与腰线平行。"
        ],
        "proportion": "前脸接近 1.8:1，驾驶室偏高窄（估）。",
        "cmf": "车身同色漆，格栅镀铬，轮拱同色。",
        "judgement": "平直折线让前脸显干练。",
        "style_tags": [
         {
          "tag": "扎实",
          "cluster": "stability",
          "evidence": "保险杠下沿通长平直"
         },
         {
          "tag": "方峻",
          "cluster": "tough",
          "evidence": "灯腔与面罩成直角"
         },
         {
          "tag": "规整",
          "cluster": "precision",
          "evidence": "饰条等距平行"
         }
        ]
       },
       "parts": [
        {
         "slot": "grille",
         "label": "grille",
         "term": "横置多层格栅",
         "aliases": [
          "多横幅格栅"
         ],
         "part_family": "sheet_metal",
         "family_reason": "两层横向板条",
         "visible": "full",
         "bbox": [
          80,
          400,
          210,
          570
         ],
         "form": [
          "两道横向饰条压在上三分之一，镀铬包边。",
          "板条间距一致，止于灯腔内缘。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "镀铬与哑黑"
         },
         "intent": "横向饰条拉宽前脸，镀铬提亮上沿。"
        },
        {
         "slot": "bumper",
         "label": "bumper",
         "term": "整体式保险杠",
         "aliases": [
          "一体式前包围"
         ],
         "part_family": "sheet_metal",
         "family_reason": "单一连续件",
         "visible": "full",
         "bbox": [
          30,
          590,
          240,
          730
         ],
         "form": [
          "单一连续件包住车头下部，下沿通长平直。",
          "两端不外抛，与轮眉齐平。"
         ],
         "cmf": {
          "material_class": "钢板",
          "finish": "同色漆"
         },
         "intent": "平直下沿保持离地间隙，便于判断接近角。"
        },
        {
         "slot": "side_guard",
         "label": "side_guard",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "wheel_arch",
         "label": "wheel_arch",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        },
        {
         "slot": "step",
         "label": "step",
         "term": null,
         "aliases": [],
         "part_family": null,
         "family_reason": null,
         "visible": "not_visible",
         "bbox": null,
         "form": null,
         "cmf": null,
         "intent": null
        }
       ],
       "unplaced": []
      }
     }
    ]
   }
  ]
 },
 "s3": {
  "fixture": "s3-report",
  "version": "1.0",
  "generated_at": "2026-11-05",
  "notice": "模拟数据：用于高保真填充与联调，数值与文案按真实链路的结构生成，不代表真实检索结果。生成脚本 scripts/make_ui_fixtures.py",
  "contract": "docs/ui-fixture-spec.md",
  "meta": {
   "category": "沙漠牵引车",
   "aspect": "16:9",
   "total": 12,
   "title": "沙漠牵引车 · 竞品设计分析"
  },
  "pages": [
   {
    "id": "p01",
    "type": "cover",
    "title": "沙漠牵引车",
    "subtitle": "竞品设计分析 · 2026 年 11 月",
    "status": "full",
    "blocks": []
   },
   {
    "id": "p02",
    "type": "method",
    "title": "方法与来源",
    "subtitle": "四层关联 · 八台参照",
    "status": "full",
    "blocks": []
   },
   {
    "id": "p03",
    "type": "car",
    "title": "德龙 X3000",
    "subtitle": "陕汽 · 6×6 牵引车",
    "vehicle": "德龙 X3000",
    "status": "full",
    "blocks": [
     {
      "id": "title",
      "kind": "text",
      "text": "德龙 X3000"
     },
     {
      "id": "subtitle",
      "kind": "text",
      "text": "陕汽 · 6×6 牵引车"
     },
     {
      "id": "style_words",
      "kind": "tags",
      "items": [
       {
        "term": "敦实",
        "evidence": "横向饰条贯通至灯缘"
       },
       {
        "term": "硬朗",
        "evidence": "格栅直边与方形灯腔"
       },
       {
        "term": "整面化",
        "evidence": "保险杠与面罩同色连片"
       }
      ]
     },
     {
      "id": "hero",
      "kind": "image",
      "src": "../../data-test/ab-images/03-陕汽重卡-德龙X3000-6X6-沙漠越野载货车/1.jpg"
     },
     {
      "id": "parts",
      "kind": "grid",
      "items": [
       {
        "term": "横置多层格栅",
        "cmf": "钢板 · 哑黑喷涂"
       },
       {
        "term": "整体式保险杠",
        "cmf": "钢板 · 同色漆"
       },
       {
        "term": "两级固定踏板",
        "cmf": "钢板 · 防滑涂层"
       }
      ]
     },
     {
      "id": "note",
      "kind": "text",
      "text": "横向分层压住车头体量。"
     }
    ]
   },
   {
    "id": "p04",
    "type": "car",
    "title": "豪沃 TX7",
    "subtitle": "重汽 · 6×6 牵引车",
    "vehicle": "豪沃 TX7",
    "status": "full",
    "blocks": [
     {
      "id": "title",
      "kind": "text",
      "text": "豪沃 TX7"
     },
     {
      "id": "subtitle",
      "kind": "text",
      "text": "重汽 · 6×6 牵引车"
     },
     {
      "id": "style_words",
      "kind": "tags",
      "items": [
       {
        "term": "稳重",
        "evidence": "网板外框横向完整"
       },
       {
        "term": "刚直",
        "evidence": "灯腔转角接近直角"
       },
       {
        "term": "参数化",
        "evidence": "孔阵横向等距排布"
       }
      ]
     },
     {
      "id": "hero",
      "kind": "image",
      "src": "../../data-test/ab-images/15-豪沃-6x6/1.jpg"
     },
     {
      "id": "parts",
      "kind": "grid",
      "items": [
       {
        "term": "冲孔网板格栅",
        "cmf": "钢板 · 哑黑喷塑"
       },
       {
        "term": "分体式保险杠",
        "cmf": "塑料 · 同色漆与哑黑"
       },
       {
        "term": "单级固定踏板",
        "cmf": "钢板 · 防滑涂层"
       }
      ]
     },
     {
      "id": "note",
      "kind": "text",
      "text": "大面积网板压低视觉重心。"
     }
    ]
   },
   {
    "id": "p05",
    "type": "car",
    "title": "解放 JH6",
    "subtitle": "一汽 · 6×4 牵引车",
    "vehicle": "解放 JH6",
    "status": "full",
    "blocks": [
     {
      "id": "title",
      "kind": "text",
      "text": "解放 JH6"
     },
     {
      "id": "subtitle",
      "kind": "text",
      "text": "一汽 · 6×4 牵引车"
     },
     {
      "id": "style_words",
      "kind": "tags",
      "items": [
       {
        "term": "扎实",
        "evidence": "保险杠下沿通长平直"
       },
       {
        "term": "方峻",
        "evidence": "灯腔与面罩成直角"
       },
       {
        "term": "规整",
        "evidence": "饰条等距平行"
       }
      ]
     },
     {
      "id": "hero",
      "kind": "image",
      "src": "../../data-test/ab-images/10-一汽解放-JH6/1.jpg"
     },
     {
      "id": "parts",
      "kind": "grid",
      "items": [
       {
        "term": "横置多层格栅",
        "cmf": "钢板 · 镀铬与哑黑"
       },
       {
        "term": "整体式保险杠",
        "cmf": "钢板 · 同色漆"
       },
       {
        "term": "两级固定踏板",
        "cmf": "钢板 · 防滑涂层"
       }
      ]
     },
     {
      "id": "note",
      "kind": "text",
      "text": "平直折线让前脸显干练。"
     }
    ]
   },
   {
    "id": "p06",
    "type": "car",
    "title": "德龙 6X6 沙漠版",
    "subtitle": "陕汽 · 6×6 环境特化",
    "vehicle": "德龙 6X6 沙漠版",
    "status": "thin",
    "blocks": [
     {
      "id": "title",
      "kind": "text",
      "text": "德龙 6X6 沙漠版"
     },
     {
      "id": "subtitle",
      "kind": "text",
      "text": "陕汽 · 6×6 环境特化"
     },
     {
      "id": "placeholder",
      "kind": "note",
      "text": "该车型尚未完成部件分析"
     }
    ]
   },
   {
    "id": "p07",
    "type": "car",
    "title": "沙漠运输车",
    "subtitle": "重汽 · 6×6 环境特化",
    "vehicle": "沙漠运输车",
    "status": "thin",
    "blocks": [
     {
      "id": "title",
      "kind": "text",
      "text": "沙漠运输车"
     },
     {
      "id": "subtitle",
      "kind": "text",
      "text": "重汽 · 6×6 环境特化"
     },
     {
      "id": "placeholder",
      "kind": "note",
      "text": "该车型尚未完成部件分析"
     }
    ]
   },
   {
    "id": "p08",
    "type": "car",
    "title": "德龙 M3000",
    "subtitle": "陕汽 · 4×2 基型平台",
    "vehicle": "德龙 M3000",
    "status": "thin",
    "blocks": [
     {
      "id": "title",
      "kind": "text",
      "text": "德龙 M3000"
     },
     {
      "id": "subtitle",
      "kind": "text",
      "text": "陕汽 · 4×2 基型平台"
     },
     {
      "id": "placeholder",
      "kind": "note",
      "text": "该车型尚未完成部件分析"
     }
    ]
   },
   {
    "id": "p09",
    "type": "car",
    "title": "三一 STC800",
    "subtitle": "三一 · 跨车型",
    "vehicle": "三一 STC800",
    "status": "thin",
    "blocks": [
     {
      "id": "title",
      "kind": "text",
      "text": "三一 STC800"
     },
     {
      "id": "subtitle",
      "kind": "text",
      "text": "三一 · 跨车型"
     },
     {
      "id": "placeholder",
      "kind": "note",
      "text": "该车型尚未完成部件分析"
     }
    ]
   },
   {
    "id": "p10",
    "type": "car",
    "title": "天龙 KL",
    "subtitle": "东风 · 6×4 牵引车",
    "vehicle": "天龙 KL",
    "status": "thin",
    "blocks": [
     {
      "id": "title",
      "kind": "text",
      "text": "天龙 KL"
     },
     {
      "id": "subtitle",
      "kind": "text",
      "text": "东风 · 6×4 牵引车"
     },
     {
      "id": "placeholder",
      "kind": "note",
      "text": "该车型尚未完成部件分析"
     }
    ]
   },
   {
    "id": "p11",
    "type": "overview",
    "title": "竞品总览",
    "subtitle": "八台 · 前脸与部件索引",
    "status": "full",
    "blocks": []
   },
   {
    "id": "p12",
    "type": "back",
    "title": "EquipLens",
    "subtitle": "2026 · 竞品设计分析",
    "status": "full",
    "blocks": []
   }
  ]
 }
};
