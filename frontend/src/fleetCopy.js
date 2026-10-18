const en = {
  fleet: 'All conveyors', cameras: 'Manage cameras', monitor: 'Monitoring', add: 'Add conveyor', edit: 'Edit conveyor',
  title: 'Conveyor overview', description: 'Choose a belt to review its video, measurements and alerts.', search: 'Search conveyors…',
  all: 'All', attention: 'Needs attention', active: 'Enabled', disabled: 'Disabled', running: 'Running', stopped: 'Stopped', stale: 'No recent data', unavailable: 'Waiting for video',
  total: 'Registered belts', alerts: 'Pending alerts', critical: 'Critical alerts', open: 'Open monitoring', empty: 'No conveyors yet', emptyDetail: 'Register a conveyor and choose a video to begin.', noResults: 'No matching conveyors',
  name: 'Conveyor name', code: 'Identifier', camera: 'Camera name', width: 'Belt width (mm)', source: 'Video source', sample: 'Sample video', upload: 'Upload video', file: 'Video file',
  fileHelp: 'MP4 or WebM · Up to 500 MB. Videos loop for demonstration and testing.', save: 'Save conveyor', saving: 'Saving…', cancel: 'Cancel', configure: 'Configure',
  enable: 'Enable monitoring', disable: 'Pause monitoring', paused: 'Monitoring paused', manageDetail: 'One independent video source per belt. Changes apply within a few seconds.',
  loadError: 'Unable to load conveyors. Retrying…', saveError: 'Unable to save. Please try again.', sourceRequired: 'Choose a video file.', existing: 'Keep current video', saved: 'Conveyor saved.', logout: 'Log out', unknown: 'Conveyor not found', back: 'Back to overview', processing: 'Processing the selected video…',
}
const fa = {
  fleet: 'همه تسمه‌ها', cameras: 'مدیریت دوربین‌ها', monitor: 'پایش تسمه', add: 'افزودن تسمه', edit: 'ویرایش تسمه',
  title: 'نمای کلی تسمه‌ها', description: 'برای دیدن ویدیو، اندازه‌گیری‌ها و هشدارها، یک تسمه را انتخاب کنید.', search: 'جستجوی تسمه…',
  all: 'همه', attention: 'نیازمند توجه', active: 'فعال', disabled: 'غیرفعال', running: 'در حال حرکت', stopped: 'متوقف', stale: 'داده قدیمی', unavailable: 'در انتظار ویدیو',
  total: 'تسمه‌های ثبت‌شده', alerts: 'هشدارهای بررسی‌نشده', critical: 'هشدارهای بحرانی', open: 'باز کردن پایش', empty: 'هنوز تسمه‌ای ثبت نشده', emptyDetail: 'یک تسمه ثبت کنید و فایل ویدیوی آن را انتخاب کنید.', noResults: 'تسمه‌ای پیدا نشد',
  name: 'نام تسمه', code: 'شناسه', camera: 'نام دوربین', width: 'عرض تسمه (میلی‌متر)', source: 'منبع ویدیو', sample: 'ویدیوی نمونه', upload: 'بارگذاری ویدیو', file: 'فایل ویدیو',
  fileHelp: 'MP4 یا WebM · حداکثر ۵۰۰ مگابایت. ویدیوها برای نمایش و آزمایش تکرار می‌شوند.', save: 'ذخیره تسمه', saving: 'در حال ذخیره…', cancel: 'انصراف', configure: 'تنظیمات',
  enable: 'فعال کردن پایش', disable: 'توقف پایش', paused: 'پایش غیرفعال است', manageDetail: 'هر تسمه فایل ویدیوی مستقل دارد. تغییرات پس از چند ثانیه اعمال می‌شوند.',
  loadError: 'دریافت تسمه‌ها ممکن نیست؛ در حال تلاش مجدد…', saveError: 'ذخیره ممکن نشد؛ دوباره تلاش کنید.', sourceRequired: 'یک فایل ویدیو انتخاب کنید.', existing: 'حفظ ویدیوی فعلی', saved: 'تسمه ذخیره شد.', logout: 'خروج', unknown: 'تسمه پیدا نشد', back: 'بازگشت به نمای کلی', processing: 'در حال پردازش ویدیوی انتخاب‌شده…',
}
const ar = {
  ...en, fleet: 'كل السيور', cameras: 'إدارة الكاميرات', monitor: 'المراقبة', add: 'إضافة سير', edit: 'تعديل السير', title: 'نظرة عامة على السيور',
  description: 'اختر سيرًا لمراجعة الفيديو والقياسات والتنبيهات.', search: 'بحث عن سير…', all: 'الكل', attention: 'يحتاج إلى مراجعة', active: 'مفعّل', disabled: 'معطّل', running: 'يعمل', stopped: 'متوقف', stale: 'بيانات قديمة', unavailable: 'بانتظار الفيديو', total: 'السيور المسجلة', alerts: 'تنبيهات معلقة', critical: 'تنبيهات حرجة', open: 'فتح المراقبة', name: 'اسم السير', code: 'المعرّف', camera: 'اسم الكاميرا', width: 'عرض السير (مم)', source: 'مصدر الفيديو', sample: 'فيديو تجريبي', upload: 'تحميل فيديو', file: 'ملف الفيديو', save: 'حفظ', saving: 'جارٍ الحفظ…', cancel: 'إلغاء', configure: 'إعدادات', enable: 'تفعيل المراقبة', disable: 'إيقاف المراقبة', logout: 'خروج', back: 'العودة إلى النظرة العامة',
}
export const getFleetCopy = lang => lang === 'fa' ? fa : lang === 'ar' ? ar : en
