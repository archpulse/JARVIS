import json
import os

import qdarktheme
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

AI_DATA_DIR = os.path.expanduser("~/.axinix/.ai")
ENV_FILE = os.path.join(AI_DATA_DIR, ".env")
SETTINGS_FILE = os.path.join(AI_DATA_DIR, "settings.json")
PLUGIN_DAILY_LIMIT = 25

WIZARD_TRANSLATIONS = {
    "EN": {
        "page1_title": "Hello! I am Axinix AI",
        "page1_desc": "Welcome to the autonomous AI ecosystem. I’m here to help you automate your workflow and enhance your Linux experience. Let’s start by customizing your setup.",
        "lang_lbl": "Language:",
        "theme_lbl": "Theme:",
        "page2_title": 'Connecting the "Brains"',
        "page2_desc": 'To enable reasoning and code analysis, I require a Google Gemini API Key. How to get one?\n1. Visit Google AI Studio.\n2. Click "Get API key".\n3. Copy and paste it into the field below.',
        "api_placeholder": "Paste your Google Gemini API Key here...",
        "page3_title": "Ready to talk?",
        "page3_desc": 'Almost there! Once the main window opens:\n\n1. Click the [INIT] button. I will load the language models and calibrate your microphone.\n2. Wait for the "Ready" status in the top bar.\n3. Simply say "Hey Jarvis" — I’ll hear you through my local openwakeword engine and wait for your command.',
        "page4_title": "Expanding Capabilities",
        "page4_desc": f"You can ask me to search GitHub plugins. I first compare metadata and README previews, then ask for your confirmation before download. Only confirmed code that passes static checks is installed into plugins. For safety, plugin installs and AI security reviews are limited to {PLUGIN_DAILY_LIMIT} per day.",
        "page5_title": "Launching...",
        "page5_desc": 'Configuration complete! Axinix AI is now ready to serve on your system. If you have questions, check out our GitHub repository. Click "Finish" to launch the assistant!',
        "page_city_title": "Your Location",
        "page_city_desc": "Please enter your default city. I use this to know your current time, adjust my greeting tone (morning, day, evening), and fetch accurate local weather and news.",
        "city_lbl": "City:",
        "city_placeholder": "e.g., Los Angeles, Kyiv, Seoul",
    },
    "RU": {
        "page1_title": "Привет! Я Axinix AI",
        "page1_desc": "Добро пожаловать в автономную ИИ-экосистему. Я здесь, чтобы помочь автоматизировать ваш рабочий процесс и улучшить опыт работы в Linux. Давайте начнем с настройки.",
        "lang_lbl": "Язык:",
        "theme_lbl": "Тема:",
        "page2_title": 'Подключение "Мозгов"',
        "page2_desc": 'Для работы логики и анализа кода мне нужен API-ключ Google Gemini. Как его получить?\n1. Зайдите в Google AI Studio.\n2. Нажмите "Get API key".\n3. Скопируйте и вставьте его в поле ниже.',
        "api_placeholder": "Вставьте ваш Google Gemini API Key сюда...",
        "page3_title": "Готовы к разговору?",
        "page3_desc": 'Почти готово! Как только откроется главное окно:\n\n1. Нажмите кнопку [INIT]. Я загружу языковые модели и откалибрую микрофон.\n2. Дождитесь статуса "System Online" наверху.\n3. Просто скажите "Hey Jarvis" — я услышу вас через локальный движок openwakeword и буду ждать команду.',
        "page4_title": "Расширение возможностей",
        "page4_desc": f"Вы можете попросить меня искать плагины на GitHub. Сначала я сравниваю метаданные и превью README, затем запрашиваю явное подтверждение перед скачиванием. В plugins устанавливается только подтвержденный код, прошедший статическую проверку. Для безопасности действует лимит: не более {PLUGIN_DAILY_LIMIT} установок и AI-проверок плагинов в день.",
        "page5_title": "Запуск...",
        "page5_desc": 'Настройка завершена! Axinix AI готов к работе. Если у вас есть вопросы, загляните в наш репозиторий на GitHub. Нажмите "Готово", чтобы запустить ассистента!',
        "page_city_title": "Ваша локация",
        "page_city_desc": "Пожалуйста, введите ваш город по умолчанию. Это нужно, чтобы я знал ваше местное время, подстраивал тон приветствия (утро, день, вечер) и давал точные прогнозы погоды и новости.",
        "city_lbl": "Город:",
        "city_placeholder": "например, Лос-Анджелес, Киев, Seoul",
    },
    "UA": {
        "page1_title": "Привіт! Я Axinix AI",
        "page1_desc": "Ласкаво просимо до автономної ШІ-екосистеми. Я тут, щоб допомогти автоматизувати ваш робочий процес і покращити досвід роботи в Linux. Почнімо з налаштування.",
        "lang_lbl": "Мова:",
        "theme_lbl": "Тема:",
        "page2_title": 'Підключення "Мізків"',
        "page2_desc": 'Для роботи логіки та аналізу коду мені потрібен API-ключ Google Gemini. Як його отримати?\n1. Зайдіть у Google AI Studio.\n2. Натисніть "Get API key".\n3. Скопіюйте та вставте його в поле нижче.',
        "api_placeholder": "Вставте ваш Google Gemini API Key сюди...",
        "page3_title": "Готові до розмови?",
        "page3_desc": 'Майже готово! Щойно відкриється головне вікно:\n\n1. Натисніть кнопку [INIT]. Я завантажу мовні моделі та відкалібрую мікрофон.\n2. Дочекайтеся статусу "System Online" нагорі.\n3. Просто скажіть "Hey Jarvis" — я почую вас через локальний рушій openwakeword і чекатиму на команду.',
        "page4_title": "Розширення можливостей",
        "page4_desc": f"Ви можете попросити мене шукати плагіни на GitHub. Спочатку я порівнюю метадані та прев'ю README, потім запитую явне підтвердження перед завантаженням. У plugins встановлюється лише підтверджений код, що пройшов статичну перевірку. Для безпеки діє ліміт: не більше {PLUGIN_DAILY_LIMIT} встановлень і AI-перевірок плагінів на день.",
        "page5_title": "Запуск...",
        "page5_desc": 'Налаштування завершено! Axinix AI готовий до роботи. Якщо у вас є питання, загляньте в наш репозиторий на GitHub. Натисніть "Готово", щоб запустити асистента!',
        "page_city_title": "Ваша локація",
        "page_city_desc": "Будь ласка, введіть ваше місто за замовчуванням. Це потрібно, щоб я знав ваш місцевий час, підлаштовував тон вітання (ранок, день, вечір) і давав точні прогнози погоди та новини.",
        "city_lbl": "Місто:",
        "city_placeholder": "наприклад, Лос-Анджелес, Київ, Seoul",
    },
    "DE": {
        "page1_title": "Hallo! Ich bin Axinix AI",
        "page1_desc": "Willkommen im autonomen KI-Ökosystem. Ich bin hier, um Ihren Workflow zu automatisieren. Beginnen wir mit der Einrichtung.",
        "lang_lbl": "Sprache:",
        "theme_lbl": "Thema:",
        "page2_title": 'Verbindung der "Gehirne"',
        "page2_desc": 'Für die Logik benötige ich einen Google Gemini API-Schlüssel.\n1. Besuchen Sie Google AI Studio.\n2. Klicken Sie auf "Get API key".\n3. Fügen Sie ihn unten ein.',
        "api_placeholder": "Google Gemini API Key hier einfügen...",
        "page3_title": "Bereit zum Reden?",
        "page3_desc": 'Fast fertig! Im Hauptfenster:\n\n1. Klicken Sie auf [INIT].\n2. Warten Sie auf "System Online".\n3. Sagen Sie "Hey Jarvis".',
        "page4_title": "Funktionen erweitern",
        "page4_desc": f"Sie koennen mich bitten, Plugins auf GitHub zu suchen. Ich lade den Code, pruefe ihn statisch und installiere nur Dateien automatisch, die die Sicherheitsrichtlinie bestehen. Aus Sicherheitsgruenden sind Plugin-Installationen und KI-Pruefungen auf {PLUGIN_DAILY_LIMIT} pro Tag begrenzt.",
        "page5_title": "Starten...",
        "page5_desc": 'Einrichtung abgeschlossen! Axinix AI ist bereit. Klicken Sie auf "Finish".',
        "page_city_title": "Ihr Standort",
        "page_city_desc": "Bitte geben Sie Ihre Standardstadt ein. Ich verwende dies für Wetter, Nachrichten und die Anpassung meiner Begrüßung an Ihre Tageszeit.",
        "city_lbl": "Stadt:",
        "city_placeholder": "z. B. Los Angeles, Kyjiw, Seoul",
    },
    "ES": {
        "page1_title": "¡Hola! Soy Axinix AI",
        "page1_desc": "Bienvenido al ecosistema de IA autónoma. Estoy aquí para ayudar a automatizar su flujo de trabajo. Comencemos con la configuración.",
        "lang_lbl": "Idioma:",
        "theme_lbl": "Tema:",
        "page2_title": 'Conectando los "Cerebros"',
        "page2_desc": 'Para la lógica, necesito una clave API de Google Gemini.\n1. Visite Google AI Studio.\n2. Haga clic en "Get API key".\n3. Péguela abajo.',
        "api_placeholder": "Pegue su Google Gemini API Key aquí...",
        "page3_title": "¿Listo para hablar?",
        "page3_desc": '¡Casi listo! En la ventana principal:\n\n1. Haga clic en [INIT].\n2. Espere a "System Online".\n3. Diga "Hey Jarvis".',
        "page4_title": "Ampliando capacidades",
        "page4_desc": f"Puede pedirme buscar plugins en GitHub. Descargo el codigo, aplico verificacion estatica estricta e instalo automaticamente solo archivos que pasen la politica de seguridad. Por seguridad, las instalaciones y revisiones AI de plugins estan limitadas a {PLUGIN_DAILY_LIMIT} por dia.",
        "page5_title": "Lanzamiento...",
        "page5_desc": '¡Configuración completa! Axinix AI está listo. Haga clic en "Finish".',
        "page_city_title": "Su ubicación",
        "page_city_desc": "Ingrese su ciudad predeterminada. Utilizo esto para conocer su hora actual, ajustar mi tono de saludo y obtener el clima y las noticias locales precisas.",
        "city_lbl": "Ciudad:",
        "city_placeholder": "p. ej., Los Angeles, Kyiv, Seoul",
    },
    "FR": {
        "page1_title": "Bonjour ! Je suis Axinix AI",
        "page1_desc": "Bienvenue dans l'écosystème d'IA autonome. Je suis là pour automatiser votre flux de travail. Commençons la configuration.",
        "lang_lbl": "Langue :",
        "theme_lbl": "Thème :",
        "page2_title": 'Connexion des "Cerveaux"',
        "page2_desc": "Pour la logique, j'ai besoin d'une clé API Google Gemini.\n1. Visitez Google AI Studio.\n2. Cliquez sur \"Get API key\".\n3. Collez-la ci-dessous.",
        "api_placeholder": "Collez votre Google Gemini API Key ici...",
        "page3_title": "Prêt à parler ?",
        "page3_desc": 'Presque terminé ! Dans la fenêtre principale :\n\n1. Cliquez sur [INIT].\n2. Attendez "System Online".\n3. Dites "Hey Jarvis".',
        "page4_title": "Extension des capacités",
        "page4_desc": f"Vous pouvez me demander de chercher des plugins sur GitHub. Je telecharge le code, j'applique une verification statique stricte et je n'installe automatiquement que les fichiers qui passent la politique de securite. Pour la securite, les installations et verifications IA de plugins sont limitees a {PLUGIN_DAILY_LIMIT} par jour.",
        "page5_title": "Lancement...",
        "page5_desc": 'Configuration terminée ! Axinix AI est prêt. Cliquez sur "Finish".',
        "page_city_title": "Votre emplacement",
        "page_city_desc": "Veuillez entrer votre ville par défaut. J'utilise cela pour la météo, les actualités et pour adapter mes salutations à votre heure locale.",
        "city_lbl": "Ville :",
        "city_placeholder": "par ex., Los Angeles, Kyiv, Seoul",
    },
    "ZH": {
        "page1_title": "你好！我是 Axinix AI",
        "page1_desc": "欢迎来到自治人工智能生态系统。我在这里帮助自动化您的工作流程。让我们开始设置吧。",
        "lang_lbl": "语言：",
        "theme_lbl": "主题：",
        "page2_title": "连接“大脑”",
        "page2_desc": "为了实现逻辑，我需要一个 Google Gemini API 密钥。\n1. 访问 Google AI Studio。\n2. 点击“Get API key”。\n3. 粘贴在下面。",
        "api_placeholder": "在此处粘贴您的 Google Gemini API 密钥...",
        "page3_title": "准备好说话了吗？",
        "page3_desc": "快完成了！在主窗口中：\n\n1. 点击 [INIT]。\n2. 等待“System Online”。\n3. 说“Hey Jarvis”。",
        "page4_title": "扩展能力",
        "page4_desc": f"你可以让我在 GitHub 上搜索插件。我会下载代码并执行严格静态检查，只会自动安装通过安全策略的文件。出于安全考虑，插件安装和 AI 安全检查每天最多 {PLUGIN_DAILY_LIMIT} 次。",
        "page5_title": "启动...",
        "page5_desc": "设置完成！Axinix AI 已准备就绪。点击“Finish”。",
        "page_city_title": "您的位置",
        "page_city_desc": "请输入您的默认城市。我用它来了解您的当前时间，调整我的问候语气（早晨、白天、晚上），并获取准确的当地天气和新闻。",
        "city_lbl": "城市：",
        "city_placeholder": "例如：洛杉矶，基辅，Seoul",
    },
    "JA": {
        "page1_title": "こんにちは！Axinix AI です",
        "page1_desc": "自律型AIエコシステムへようこそ。ワークフローの自動化をお手伝いします。セットアップを始めましょう。",
        "lang_lbl": "言語:",
        "theme_lbl": "テーマ:",
        "page2_title": "「頭脳」の接続",
        "page2_desc": "ロジックのために、Google Gemini APIキーが必要です。\n1. Google AI Studioにアクセスします。\n2. 「Get API key」をクリックします。\n3. 下に貼り付けます。",
        "api_placeholder": "ここに Google Gemini API キーを貼り付けてください...",
        "page3_title": "話す準備はできましたか？",
        "page3_desc": "ほぼ完了です！メインウィンドウで：\n\n1. [INIT] をクリックします。\n2. 「System Online」を待ちます。\n3. 「Hey Jarvis」と言います。",
        "page4_title": "機能の拡張",
        "page4_desc": f"GitHubのプラグイン検索を依頼できます。コードを取得して厳格な静的チェックを行い、安全ポリシーを通過したファイルのみ自動インストールします。安全のため、プラグインのインストールとAIセキュリティ確認は1日{PLUGIN_DAILY_LIMIT}回までです。",
        "page5_title": "起動中...",
        "page5_desc": "セットアップ完了！Axinix AI の準備ができました。「Finish」をクリックしてください。",
        "page_city_title": "あなたの場所",
        "page_city_desc": "デフォルトの都市を入力してください。これは、あなたの現在時刻を知り、挨拶のトーン（朝、昼、夜）を調整し、正確な現地の天気やニュースを取得するために使用されます。",
        "city_lbl": "都市:",
        "city_placeholder": "例：ロサンゼルス、キエフ、Seoul",
    },
    "KO": {
        "page1_title": "안녕하세요! Axinix AI입니다",
        "page1_desc": "자율 AI 생태계에 오신 것을 환영합니다. 워크플로우 자동화를 돕겠습니다. 설정을 시작하겠습니다.",
        "lang_lbl": "언어:",
        "theme_lbl": "테마:",
        "page2_title": '"두뇌" 연결',
        "page2_desc": '논리를 위해 Google Gemini API 키가 필요합니다.\n1. Google AI Studio를 방문하세요.\n2. "Get API key"를 클릭하세요.\n3. 아래에 붙여넣으세요.',
        "api_placeholder": "여기에 Google Gemini API 키를 붙여넣으세요...",
        "page3_title": "말할 준비가 되셨나요?",
        "page3_desc": '거의 다 되었습니다! 메인 창에서:\n\n1. [INIT]을 클릭합니다.\n2. "System Online"을 기다립니다.\n3. "Hey Jarvis"라고 말합니다.',
        "page4_title": "기능 확장",
        "page4_desc": f"GitHub plugin geomsageul butakhal su isseoyo. Kodeureul daunbatgo eomgyeokhan jeongjeok geomsa hu boan jeongchaegeul tonggwahan pailman jadongeuro seolchihamnida. Boaneul wihae plugin seolchi mit AI geomsa neun haru choedae {PLUGIN_DAILY_LIMIT}hoimnida.",
        "page5_title": "시작...",
        "page5_desc": '설정 완료! Axinix AI이 준비되었습니다. "Finish"를 클릭하세요.',
        "page_city_title": "위치",
        "page_city_desc": "기본 도시를 입력하세요. 저는 이것을 사용하여 현재 시간을 알고, 인사 톤(아침, 낮, 저녁)을 조정하고, 정확한 현지 날씨와 뉴스를 가져옵니다.",
        "city_lbl": "도시:",
        "city_placeholder": "예: 로스앤젤레스, 키예프, Seoul",
    },
    "PT": {
        "page1_title": "Olá! Eu sou Axinix AI",
        "page1_desc": "Bem-vindo ao ecossistema de IA autônoma. Estou aqui para ajudar a automatizar seu fluxo de trabalho. Vamos começar a configuração.",
        "lang_lbl": "Idioma:",
        "theme_lbl": "Tema:",
        "page2_title": 'Conectando os "Cérebros"',
        "page2_desc": 'Para a lógica, preciso de uma chave API do Google Gemini.\n1. Visite o Google AI Studio.\n2. Clique em "Get API key".\n3. Cole abaixo.',
        "api_placeholder": "Cole sua Google Gemini API Key aqui...",
        "page3_title": "Pronto para falar?",
        "page3_desc": 'Quase lá! Na janela principal:\n\n1. Clique em [INIT].\n2. Aguarde "System Online".\n3. Diga "Hey Jarvis".',
        "page4_title": "Expandindo Recursos",
        "page4_desc": f"Voce pode pedir busca de plugins no GitHub. Eu baixo o codigo, aplico verificacao estatica rigorosa e instalo automaticamente apenas arquivos que passam na politica de seguranca. Por seguranca, instalacoes e revisoes de plugins por IA sao limitadas a {PLUGIN_DAILY_LIMIT} por dia.",
        "page5_title": "Iniciando...",
        "page5_desc": 'Configuração concluída! Axinix AI está pronto. Clique em "Finish".',
        "page_city_title": "Sua localização",
        "page_city_desc": "Por favor, insira sua cidade padrão. Eu uso isso para saber sua hora atual, ajustar meu tom de saudação e buscar previsões do tempo e notícias locais precisas.",
        "city_lbl": "Cidade:",
        "city_placeholder": "ex., Los Angeles, Kiev, Seoul",
    },
    "IT": {
        "page1_title": "Ciao! Sono Axinix AI",
        "page1_desc": "Benvenuto nell'ecosistema di intelligenza artificiale autonoma. Sono qui per automatizzare il tuo flusso di lavoro. Iniziamo la configurazione.",
        "lang_lbl": "Lingua:",
        "theme_lbl": "Tema:",
        "page2_title": 'Collegamento dei "Cervelli"',
        "page2_desc": 'Per la logica, mi serve una chiave API di Google Gemini.\n1. Visita Google AI Studio.\n2. Clicca su "Get API key".\n3. Incollala qui sotto.',
        "api_placeholder": "Incolla qui la tua Google Gemini API Key...",
        "page3_title": "Pronto a parlare?",
        "page3_desc": 'Quasi finito! Nella finestra principale:\n\n1. Clicca su [INIT].\n2. Attendi "System Online".\n3. Dì "Hey Jarvis".',
        "page4_title": "Espansione delle capacità",
        "page4_desc": f"Puoi chiedermi di cercare plugin su GitHub. Scarico il codice, eseguo controlli statici rigorosi e installo automaticamente solo i file che superano la politica di sicurezza. Per sicurezza, installazioni e revisioni AI dei plugin sono limitate a {PLUGIN_DAILY_LIMIT} al giorno.",
        "page5_title": "Avvio...",
        "page5_desc": 'Configurazione completata! Axinix AI è pronto. Clicca su "Finish".',
        "page_city_title": "La tua posizione",
        "page_city_desc": "Inserisci la tua città predefinita. Lo uso per il meteo, le notizie e per adattare il mio saluto alla tua ora locale.",
        "city_lbl": "Città:",
        "city_placeholder": "ad es., Los Angeles, Kiev, Seoul",
    },
}


class WelcomePage(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle("Hello! I am Axinix AI")
        layout = QVBoxLayout()

        self.label = QLabel(
            "Welcome to the autonomous AI ecosystem. I’m here to help you automate your workflow and enhance your Linux experience. Let’s start by customizing your setup."
        )
        self.label.setWordWrap(True)
        self.label.setMargin(10)
        layout.addWidget(self.label)

        self.lang_lbl = QLabel("Language:")
        layout.addWidget(self.lang_lbl)
        self.lang_cb = QComboBox()
        self.lang_cb.addItems(
            ["EN", "RU", "UA", "DE", "ES", "FR", "ZH", "JA", "KO", "PT", "IT"]
        )
        self.lang_cb.currentTextChanged.connect(self.wizard.update_language)
        layout.addWidget(self.lang_cb)

        self.theme_lbl = QLabel("Theme:")
        layout.addWidget(self.theme_lbl)
        self.theme_cb = QComboBox()
        self.theme_cb.addItems(["Dark", "Light", "Gray"])
        self.theme_cb.currentTextChanged.connect(self.update_theme)
        layout.addWidget(self.theme_cb)

        self.setLayout(layout)

        self.registerField("language", self.lang_cb, "currentText")
        self.registerField("theme", self.theme_cb, "currentText")

    def update_theme(self, theme_name):
        theme_map = {"Dark": "dark", "Light": "light", "Gray": "gray"}
        QApplication.instance().setStyleSheet(
            qdarktheme.load_stylesheet(theme_map.get(theme_name, "dark"))
        )

    def translate(self, lang):
        t = WIZARD_TRANSLATIONS.get(lang, WIZARD_TRANSLATIONS["EN"])
        self.setTitle(t["page1_title"])
        self.label.setText(t["page1_desc"])
        self.lang_lbl.setText(t["lang_lbl"])
        self.theme_lbl.setText(t["theme_lbl"])


class CityPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Your Location")
        layout = QVBoxLayout()

        self.label = QLabel(
            "Please enter your default city. I use this to know your current time, adjust my greeting tone (morning, day, evening), and fetch accurate local weather and news."
        )
        self.label.setWordWrap(True)
        self.label.setMargin(10)
        layout.addWidget(self.label)

        self.city_lbl = QLabel("City:")
        layout.addWidget(self.city_lbl)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("e.g., London, Los Angeles, Tokyo")
        layout.addWidget(self.city_input)

        self.setLayout(layout)
        self.registerField("city*", self.city_input)  # * makes it mandatory

    def translate(self, lang):
        t = WIZARD_TRANSLATIONS.get(lang, WIZARD_TRANSLATIONS["EN"])
        self.setTitle(t["page_city_title"])
        self.label.setText(t["page_city_desc"])
        self.city_lbl.setText(t["city_lbl"])
        self.city_input.setPlaceholderText(t["city_placeholder"])


class ApiPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle('Connecting the "Brains"')
        layout = QVBoxLayout()

        self.label = QLabel(
            'To enable reasoning and code analysis, I require a Google Gemini API Key. How to get one?\n1. Visit Google AI Studio.\n2. Click "Get API key".\n3. Copy and paste it into the field below.'
        )
        self.label.setWordWrap(True)
        self.label.setMargin(10)
        layout.addWidget(self.label)

        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Paste your Google Gemini API Key here...")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_input)

        self.setLayout(layout)
        self.registerField("api_key*", self.api_input)  # * makes it mandatory

    def translate(self, lang):
        t = WIZARD_TRANSLATIONS.get(lang, WIZARD_TRANSLATIONS["EN"])
        self.setTitle(t["page2_title"])
        self.label.setText(t["page2_desc"])
        self.api_input.setPlaceholderText(t["api_placeholder"])


class FirstStartPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Ready to talk?")
        layout = QVBoxLayout()

        self.label = QLabel(
            'Almost there! Once the main window opens:\n\n1. Click the [INIT] button. I will load the language models and calibrate your microphone.\n2. Wait for the "Ready" status in the top bar.\n3. Simply say "Hey Jarvis" — I’ll hear you through my local openwakeword engine and wait for your command.'
        )
        self.label.setWordWrap(True)
        self.label.setMargin(10)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def translate(self, lang):
        t = WIZARD_TRANSLATIONS.get(lang, WIZARD_TRANSLATIONS["EN"])
        self.setTitle(t["page3_title"])
        self.label.setText(t["page3_desc"])


class PluginSystemPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Expanding Capabilities")
        layout = QVBoxLayout()

        self.label = QLabel(
            "You can ask me to search GitHub plugins. I first compare metadata and README previews, then ask for your confirmation before download. Only confirmed code that passes static checks is installed into plugins."
        )
        self.label.setWordWrap(True)
        self.label.setMargin(10)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def translate(self, lang):
        t = WIZARD_TRANSLATIONS.get(lang, WIZARD_TRANSLATIONS["EN"])
        self.setTitle(t["page4_title"])
        self.label.setText(t["page4_desc"])


class AllSetPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Launching...")
        layout = QVBoxLayout()

        self.label = QLabel(
            'Configuration complete! Axinix AI is now ready to serve on your system. If you have questions, check out our GitHub repository. Click "Finish" to launch the assistant!'
        )
        self.label.setWordWrap(True)
        self.label.setMargin(10)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def translate(self, lang):
        t = WIZARD_TRANSLATIONS.get(lang, WIZARD_TRANSLATIONS["EN"])
        self.setTitle(t["page5_title"])
        self.label.setText(t["page5_desc"])


class SetupWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Axinix AI Setup")

        # Apply qdarktheme immediately to this window

        self.setStyleSheet(
            qdarktheme.load_stylesheet("dark")
            + """
            QWizard {
                background-color: #202124;
            }
            QWizardPage {
                background-color: #202124;
            }
            QLabel {
                font-size: 14px;
                color: #e8eaed;
            }
            QComboBox, QLineEdit {
                padding: 8px 12px;
                border: 1px solid #5f6368;
                border-radius: 4px;
                background-color: #202124;
                color: #e8eaed;
                font-size: 14px;
                min-height: 20px;
                margin-bottom: 5px;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #9aa0a6;
            }
            QComboBox QAbstractItemView {
                background-color: #292a2d;
                color: #e8eaed;
                selection-background-color: #8ab4f8;
                selection-color: #202124;
                border: 1px solid #5f6368;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 1px solid #8ab4f8;
            }
            QPushButton {
                background-color: transparent;
                color: #8ab4f8;
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(138, 180, 248, 0.08);
            }
            QPushButton:pressed {
                background-color: rgba(138, 180, 248, 0.12);
            }
            QPushButton:disabled {
                color: #5f6368;
                border-color: #3c4043;
            }
        """
        )

        self.setWindowIcon(QIcon("logo.png"))
        self.resize(600, 450)

        self.page1 = WelcomePage(self)
        self.page_city = CityPage()
        self.page2 = ApiPage()
        self.page3 = FirstStartPage()
        self.page4 = PluginSystemPage()
        self.page5 = AllSetPage()

        self.addPage(self.page1)
        self.addPage(self.page_city)
        self.addPage(self.page2)
        self.addPage(self.page3)
        self.addPage(self.page4)
        self.addPage(self.page5)

        # Removed ModernStyle to allow qdarktheme to take over
        self.setOptions(
            QWizard.WizardOption.NoCancelButton | QWizard.WizardOption.IndependentPages
        )

    def update_language(self, lang):
        # Update buttons translation manually if possible
        if lang == "RU":
            self.setButtonText(QWizard.WizardButton.NextButton, "Далее >")
            self.setButtonText(QWizard.WizardButton.BackButton, "< Назад")
            self.setButtonText(QWizard.WizardButton.FinishButton, "Готово")
        elif lang == "UA":
            self.setButtonText(QWizard.WizardButton.NextButton, "Далі >")
            self.setButtonText(QWizard.WizardButton.BackButton, "< Назад")
            self.setButtonText(QWizard.WizardButton.FinishButton, "Готово")
        else:
            self.setButtonText(QWizard.WizardButton.NextButton, "Next >")
            self.setButtonText(QWizard.WizardButton.BackButton, "< Back")
            self.setButtonText(QWizard.WizardButton.FinishButton, "Finish")

        self.page1.translate(lang)
        self.page_city.translate(lang)
        self.page2.translate(lang)
        self.page3.translate(lang)
        self.page4.translate(lang)
        self.page5.translate(lang)

    def accept(self):
        api_key = self.field("api_key")
        language = self.field("language")
        theme_idx = self.field("theme")
        city = self.field("city")

        theme_map = {"Dark": "dark", "Light": "light", "Gray": "gray"}
        theme_val = theme_map.get(theme_idx, "dark")

        if api_key:
            os.makedirs(AI_DATA_DIR, exist_ok=True)
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(f"GOOGLE_API_KEY={api_key}\n")

            # Update running environment variable so the main process immediately sees it
            os.environ["GOOGLE_API_KEY"] = api_key

        settings = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Setup settings read error: {e}")

        settings["lang"] = language if language else "EN"
        settings["theme"] = theme_val
        settings["city"] = city if city else ""
        settings["first_run_completed"] = True

        os.makedirs(AI_DATA_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)

        super().accept()


def run_wizard_if_needed():
    first_run = True
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("first_run_completed"):
                    first_run = False
        except (json.JSONDecodeError, OSError) as e:
            print(f"Wizard startup settings read error: {e}")

    if first_run:
        QApplication.instance().setStyleSheet(qdarktheme.load_stylesheet("dark"))
        wizard = SetupWizard()
        wizard.exec()
