import type {RegionEconomy, RouteSeason} from './additional-types';

export const sectorNames: Record<string, string> = {
  A:'Сельское и лесное хозяйство', B:'Добыча', C:'Обрабатывающие производства',
  D:'Энергетика', E:'Вода и отходы', F:'Строительство', G:'Торговля', H:'Транспорт и хранение',
  I:'Гостиницы и питание', J:'Информация и связь', K:'Финансы и страхование', L:'Недвижимость',
  M:'Профессиональная деятельность', N:'Административные услуги', O:'Государственное управление',
  P:'Образование', Q:'Здравоохранение', R:'Культура и спорт', S:'Другие услуги',
  T:'Домашние хозяйства', U:'Экстерриториальные организации', unknown:'Отрасль не указана',
};

export const formatNumber = (value: number | null | undefined, digits = 0) =>
  value == null || !Number.isFinite(value) ? 'Нет данных' : new Intl.NumberFormat('ru-RU', {maximumFractionDigits: digits}).format(value);
export const money = (value: number | null | undefined) => value == null ? 'Нет данных' : `${formatNumber(value / 1e9, 2)} млрд ₽`;

export function selectedEconomy(regions: RegionEconomy[], region: string, sector: string) {
  const selected = regions.filter(r => region === 'all' || r.region_id === region);
  const rows: Pick<RegionEconomy,'company_rows'|'strict_rows'|'strict_revenue_rows'|'strict_revenue_rub'>[] = selected.flatMap<Pick<RegionEconomy,'company_rows'|'strict_rows'|'strict_revenue_rows'|'strict_revenue_rub'>>(r => sector === 'all' ? [r] : r.sectors.filter(s => s.sector === sector));
  const sum = (key: 'company_rows' | 'strict_rows' | 'strict_revenue_rows') => rows.reduce((a, r) => a + r[key], 0);
  const known = rows.filter(r => r.strict_revenue_rub != null);
  return {company_rows:sum('company_rows'), strict_rows:sum('strict_rows'), revenue_rows:sum('strict_revenue_rows'),
    revenue:known.length ? known.reduce((a,r) => a + r.strict_revenue_rub!,0) : null};
}

export type SeasonState = {kind:'window'|'restricted'|'closed'|'unknown'|'scenario'; label:string; detail:string};
export function seasonState(row: RouteSeason, day: string, tonnes: number, scenario: boolean): SeasonState {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !Number.isFinite(tonnes) || tonnes <= 0) {
    return {kind:'unknown',label:'Укажите дату и массу',detail:'Масса автомобиля должна быть больше нуля.'};
  }
  if (scenario) return {kind:'scenario',label:'Сценарий: круглогодичная связь',detail:`Предполагается проезд автомобиля ${tonnes} т в выбранную дату. Стоимость и техническая реализуемость не оценены.`};
  if (!row.opening_date || day < row.opening_date || day > row.report_date) {
    return {kind:'unknown',label:'Нет наблюдения на эту дату',detail:`Источник описывает сезон до ${row.report_date}. Данные не продлеваются автоматически на другие даты.`};
  }
  if (row.closure_date && day >= row.closure_date) {
    return {kind:'closed',label:'Закрыт по источнику',detail:`Дата закрытия: ${row.closure_date}. Альтернативные перевозки этим наблюдением не описаны.`};
  }
  if (row.weight_limit_tonnes != null && row.restriction_start_date && day >= row.restriction_start_date && tonnes > row.weight_limit_tonnes) {
    return {kind:'restricted',label:'Масса превышает ограничение',detail:`С ${row.restriction_start_date} опубликовано ограничение ${row.weight_limit_tonnes} т.`};
  }
  return {kind:'window',label:'В периоде эксплуатации',detail:row.weight_limit_tonnes != null && row.restriction_start_date && day >= row.restriction_start_date
    ? `Масса не превышает опубликованные ${row.weight_limit_tonnes} т. Промежуточные закрытия могут быть не учтены.`
    : 'Дата попадает между открытием и последним наблюдением/закрытием. Допустимая масса на эту дату не подтверждена.'};
}

// Only the published winter schedule format is accepted. Unknown notation
// returns null rather than silently assuming daily operation.
export function flightOnDate(row: Record<string,string|null>, day:string): boolean | null {
  if (!day || day < (row.season_start || '') || day > (row.season_end || '')) return false;
  const raw = (row.validity_raw || '').trim();
  const inSeason = (dm:string) => {
    const [d,m] = dm.split('.').map(Number);
    const startYear = Number(row.season_start?.slice(0,4));
    const startMonth = Number(row.season_start?.slice(5,7));
    return `${startYear + (m < startMonth ? 1 : 0)}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
  };
  const range = raw.match(/^(\d{2}\.\d{2})\s*-\s*(\d{2}\.\d{2})$/);
  if (range) {
    if (day < inSeason(range[1]) || day > inSeason(range[2])) return false;
    const weekdays = (row.weekdays_raw || '').split(/[,\s]+/).filter(Boolean);
    if (!weekdays.length || weekdays.some(w => !['ВС','ПН','ВТ','СР','ЧТ','ПТ','СБ'].includes(w))) return null;
    return weekdays.includes(['ВС','ПН','ВТ','СР','ЧТ','ПТ','СБ'][new Date(`${day}T12:00:00Z`).getUTCDay()]);
  }
  if (/^\d{2}\.\d{2}(?:[\s/]+\d{2}\.\d{2})*$/.test(raw)) {
    return (raw.match(/\d{2}\.\d{2}/g) || []).some(dm => inSeason(dm) === day);
  }
  return null;
}
