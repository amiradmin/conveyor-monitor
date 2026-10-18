import { useState } from 'react'
import './beltForecast.css'
const texts = {
 fa: ['پیش‌بینی سلامت و عمر تسمه','نمایش مفهومی · داده‌های نمونه','شاخص سلامت تسمه','عمر باقی‌مانده برآوردی','ساعت کار','خطر پیشرفت آسیب','بالا','ارزیابی آسیب‌های نمونه','بریدگی لبه تسمه','ترک سطحی','سایش موضعی','خطر بالا','خطر متوسط','خطر پایین','روند آسیب','در حال رشد','رشد آهسته','پایدار','اقدام پیشنهادی','بازرسی در اولین توقف برنامه‌ریزی‌شده','بازبینی اندازه ترک در شیفت بعد','بررسی در سرویس دوره‌ای','این اعداد صرفاً برای ارائه ایده هستند و از دوربین یا داده‌های عملیاتی محاسبه نشده‌اند.','نیازمند پایش و بازبینی','۱ آسیب با اولویت بررسی بالا'],
 en: ['Belt health & life forecast','Concept preview · Sample data','Belt health score','Estimated remaining life','operating hours','Damage progression risk','High','Sample damage assessment','Belt edge cut','Surface crack','Localized wear','High risk','Medium risk','Low risk','Damage trend','Growing','Slow growth','Stable','Suggested action','Inspect at the next planned stop','Review crack size next shift','Review at routine service','These figures illustrate the concept only. They are not calculated from camera or operational data.','Monitoring and review advised','1 damage with high review priority'],
 ar: ['توقع صحة الحزام وعمره','معاينة مفاهيمية · بيانات تجريبية','مؤشر صحة الحزام','العمر المتبقي التقديري','ساعة تشغيل','خطر تطور التلف','مرتفع','تقييم التلف التجريبي','قطع في حافة الحزام','شق سطحي','تآكل موضعي','خطر مرتفع','خطر متوسط','خطر منخفض','اتجاه التلف','متزايد','نمو بطيء','مستقر','الإجراء المقترح','الفحص عند التوقف المخطط التالي','مراجعة حجم الشق في الوردية التالية','المراجعة أثناء الصيانة الدورية','هذه الأرقام لعرض الفكرة فقط ولا يتم حسابها من الكاميرا أو بيانات التشغيل.','يُنصح بالمراقبة والمراجعة','تلف واحد بأولوية مراجعة عالية'],
}
export default function BeltForecast({ lang }) {
 const [selected, setSelected] = useState(0)
 const c = texts[lang] || texts.en
 const n = value => new Intl.NumberFormat(lang === 'fa' ? 'fa-IR' : lang === 'ar' ? 'ar' : 'en').format(value)
 return <section className="belt-forecast" aria-labelledby="forecast-title">
  <div className="forecast-heading"><h2 id="forecast-title">{c[0]}</h2><span className="forecast-demo">{c[1]}</span></div>
  <div className="forecast-metrics">
   <div className="forecast-metric"><span>{c[2]}</span><strong>{n(72)}<small> / {n(100)}</small></strong><div className="forecast-health-track"><i /></div><p>{c[23]}</p></div>
   <div className="forecast-metric"><span>{c[3]}</span><strong dir="ltr">{n(300)}–{n(500)}</strong><small>{c[4]}</small></div>
   <div className="forecast-metric"><span>{c[5]}</span><strong className="forecast-high">{c[6]}</strong><p>{c[24]}</p></div>
  </div>
  <h3>{c[7]}</h3>
  <div className="forecast-damage-layout"><div className="forecast-damage-list">{[0,1,2].map(i => <button type="button" key={i} aria-pressed={selected === i} className={`forecast-damage ${selected === i ? 'selected' : ''}`} onClick={() => setSelected(i)}><span><strong>{c[8+i]}</strong><small><bdi>D-0{i+1}</bdi></small></span><span className={`forecast-risk risk-${i}`}>{c[11+i]}</span></button>)}</div>
   <div className="forecast-detail" aria-live="polite"><h4>{c[8+selected]} · <bdi>D-0{selected+1}</bdi></h4><dl><div><dt>{c[14]}</dt><dd>{c[15+selected]}</dd></div><div><dt>{c[18]}</dt><dd>{c[19+selected]}</dd></div></dl></div>
  </div><p className="forecast-note">{c[22]}</p>
 </section>
}
