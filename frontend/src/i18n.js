export const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English', short: 'EN' },
  { code: 'fa', label: 'فارسی', short: 'FA' },
  { code: 'ar', label: 'العربية', short: 'AR' },
]

export const RTL_LANGUAGES = new Set(['fa', 'ar'])

export const translations = {
  en: {
    appName: 'Conveyor AI Monitor', asset: 'CV-01',
    home: 'Home', liveVision: 'Live Vision', events: 'Events', settings: 'Settings',
    systemOnline: 'System Online', allNominal: 'All systems nominal', reconnecting: 'Telemetry reconnecting',
    beltSpeed: 'Belt Speed', alignment: 'Alignment', materialFlow: 'Material Flow', overload: 'Overload',
    tearRisk: 'Tear Risk', aiConfidence: 'AI Confidence', plcReadOnly: 'PLC Read Only',
    autoRunning: 'Auto (Running)', connected: 'Connected', normal: 'NORMAL', high: 'HIGH', overloadState: 'OVERLOAD',
    recentEvents: 'Recent Events', viewAll: 'View All', operatingNormally: 'CV-01 operating normally',
    alignmentWithin: 'Alignment within range', materialStable: 'Material flow stable', overloadDetected: 'Conveyor overload detected',
    alignmentWarning: 'Alignment warning (auto-corrected)', plcConfirmed: 'PLC mode confirmed', offset: 'Offset', load: 'Load',
    logout: 'Logout', language: 'Language',
    signIn: 'Sign in', signInTitle: 'Operations Access', signInSubtitle: 'Secure access to Conveyor AI Monitor',
    username: 'Username', password: 'Password', usernamePlaceholder: 'Enter your username', passwordPlaceholder: 'Enter your password',
    signingIn: 'Signing in…', invalidCredentials: 'Invalid username or password.', loginUnavailable: 'Authentication service is unavailable.',
    secureJwt: 'JWT secured session', monitoring: 'Industrial Vision · Conveyor Monitoring',
  },
  fa: {
    appName: 'پایش هوشمند نوار نقاله', asset: 'CV-01',
    home: 'خانه', liveVision: 'نمای زنده', events: 'رویدادها', settings: 'تنظیمات',
    systemOnline: 'سیستم آنلاین', allNominal: 'همه سامانه‌ها در وضعیت عادی', reconnecting: 'در حال اتصال مجدد به تله‌متری',
    beltSpeed: 'سرعت نوار', alignment: 'هم‌راستایی', materialFlow: 'دبی مواد', overload: 'اضافه‌بار',
    tearRisk: 'ریسک پارگی', aiConfidence: 'اطمینان هوش مصنوعی', plcReadOnly: 'PLC فقط‌خواندنی',
    autoRunning: 'خودکار (در حال کار)', connected: 'متصل', normal: 'عادی', high: 'بالا', overloadState: 'اضافه‌بار',
    recentEvents: 'رویدادهای اخیر', viewAll: 'مشاهده همه', operatingNormally: 'CV-01 در وضعیت عادی کار می‌کند',
    alignmentWithin: 'هم‌راستایی در محدوده مجاز', materialStable: 'دبی مواد پایدار است', overloadDetected: 'اضافه‌بار نوار نقاله تشخیص داده شد',
    alignmentWarning: 'هشدار هم‌راستایی (اصلاح خودکار)', plcConfirmed: 'حالت PLC تأیید شد', offset: 'انحراف', load: 'بار',
    logout: 'خروج', language: 'زبان',
    signIn: 'ورود', signInTitle: 'ورود به سامانه عملیات', signInSubtitle: 'دسترسی امن به سامانه پایش هوشمند نوار نقاله',
    username: 'نام کاربری', password: 'رمز عبور', usernamePlaceholder: 'نام کاربری را وارد کنید', passwordPlaceholder: 'رمز عبور را وارد کنید',
    signingIn: 'در حال ورود…', invalidCredentials: 'نام کاربری یا رمز عبور نادرست است.', loginUnavailable: 'سرویس احراز هویت در دسترس نیست.',
    secureJwt: 'نشست امن با JWT', monitoring: 'بینایی صنعتی · پایش نوار نقاله',
  },
  ar: {
    appName: 'مراقبة الناقل بالذكاء الاصطناعي', asset: 'CV-01',
    home: 'الرئيسية', liveVision: 'الرؤية الحية', events: 'الأحداث', settings: 'الإعدادات',
    systemOnline: 'النظام متصل', allNominal: 'جميع الأنظمة تعمل بشكل طبيعي', reconnecting: 'إعادة الاتصال ببيانات القياس',
    beltSpeed: 'سرعة الحزام', alignment: 'المحاذاة', materialFlow: 'تدفق المواد', overload: 'الحمل الزائد',
    tearRisk: 'خطر التمزق', aiConfidence: 'ثقة الذكاء الاصطناعي', plcReadOnly: 'PLC للقراءة فقط',
    autoRunning: 'تلقائي (يعمل)', connected: 'متصل', normal: 'طبيعي', high: 'مرتفع', overloadState: 'حمل زائد',
    recentEvents: 'الأحداث الأخيرة', viewAll: 'عرض الكل', operatingNormally: 'CV-01 يعمل بشكل طبيعي',
    alignmentWithin: 'المحاذاة ضمن النطاق', materialStable: 'تدفق المواد مستقر', overloadDetected: 'تم اكتشاف حمل زائد على الناقل',
    alignmentWarning: 'تحذير محاذاة (تم التصحيح تلقائياً)', plcConfirmed: 'تم تأكيد وضع PLC', offset: 'الانحراف', load: 'الحمل',
    logout: 'تسجيل الخروج', language: 'اللغة',
    signIn: 'تسجيل الدخول', signInTitle: 'الدخول إلى نظام العمليات', signInSubtitle: 'وصول آمن إلى نظام مراقبة الناقل',
    username: 'اسم المستخدم', password: 'كلمة المرور', usernamePlaceholder: 'أدخل اسم المستخدم', passwordPlaceholder: 'أدخل كلمة المرور',
    signingIn: 'جارٍ تسجيل الدخول…', invalidCredentials: 'اسم المستخدم أو كلمة المرور غير صحيحة.', loginUnavailable: 'خدمة المصادقة غير متاحة.',
    secureJwt: 'جلسة آمنة باستخدام JWT', monitoring: 'الرؤية الصناعية · مراقبة الناقل',
  },
}

export function getTranslation(lang) {
  return translations[lang] || translations.en
}
