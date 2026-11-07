import test from 'node:test';
import assert from 'node:assert/strict';
import {seasonState,flightOnDate,selectedEconomy} from '../lib/additional-model.ts';

const route={opening_date:'2025-12-15',closure_date:'',report_date:'2026-03-30',weight_limit_tonnes:5,restriction_start_date:'2026-03-14'};
test('season respects observation horizon, opening, restrictions and closure',()=>{
  assert.equal(seasonState(route,'2025-12-14',10,false).kind,'unknown');
  assert.equal(seasonState(route,'2026-03-13',10,false).kind,'window');
  assert.equal(seasonState(route,'2026-03-14',10,false).kind,'restricted');
  assert.equal(seasonState(route,'2026-03-14',5,false).kind,'window');
  assert.equal(seasonState(route,'2026-03-31',5,false).kind,'unknown');
  assert.equal(seasonState({...route,closure_date:'2026-03-27'},'2026-03-27',5,false).kind,'closed');
  assert.equal(seasonState(route,'2026-03-14',10,true).kind,'scenario');
  assert.equal(seasonState(route,'2026-03-14',NaN,true).kind,'unknown');
});
test('winter flight calendar handles ranges, weekdays, new year and explicit exceptions',()=>{
  const f={season_start:'2026-10-26',season_end:'2027-03-26',validity_raw:'26.10-28.12',weekdays_raw:'ПН, ЧТ'};
  assert.equal(flightOnDate(f,'2026-11-09'),true);
  assert.equal(flightOnDate(f,'2026-11-10'),false);
  assert.equal(flightOnDate(f,'2027-01-04'),false);
  assert.equal(flightOnDate({...f,validity_raw:'29.12/12.01'},'2027-01-12'),true);
  assert.equal(flightOnDate({...f,validity_raw:'11.01-18.02'},'2027-01-11'),true);
  assert.equal(flightOnDate({...f,validity_raw:'неизвестно'},'2026-11-09'),null);
  assert.equal(flightOnDate(f,'2027-04-01'),false);
});
test('empty and all-missing revenue remain unavailable; actual zero is preserved',()=>{
  const base={region_id:'01',company_rows:2,strict_rows:1,strict_revenue_rows:0,strict_revenue_rub:null,sectors:[]};
  assert.equal(selectedEconomy([base],'01','all').revenue,null);
  assert.equal(selectedEconomy([base],'missing','all').revenue,null);
  assert.equal(selectedEconomy([{...base,strict_revenue_rows:1,strict_revenue_rub:0}],'01','all').revenue,0);
  const sector={sector:'H',company_rows:1,strict_rows:1,strict_revenue_rows:1,strict_revenue_rub:700};
  assert.equal(selectedEconomy([{...base,sectors:[sector]}],'01','H').revenue,700);
  assert.equal(selectedEconomy([{...base,sectors:[sector]}],'01','C').revenue,null);
});
