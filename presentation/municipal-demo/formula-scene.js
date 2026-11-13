function FormulaVisual({index}){
  if(index===0)return z.jsxs('div',{className:'formula-decay',children:[...[[100,'Рядом'],[50,'2 часа'],[25,'4 часа']].map(([value,label])=>z.jsxs('div',{children:[z.jsxs('span',{children:[z.jsx('i',{'data-viz':'bar',style:{width:value+'%'}}),z.jsx('b',{children:value+'%'})]}),z.jsx('small',{children:label})]},label)),z.jsx('p',{children:'Тот же рынок, меньше вклад'})]});
  if(index===1)return z.jsxs('div',{className:'formula-weight',children:[z.jsxs('div',{className:'formula-populations',children:[1,2,4].map((weight,i)=>z.jsxs('div',{children:[z.jsx('span',{'data-viz':'dot',style:{width:24+weight*10,height:24+weight*10}}),z.jsx('small',{children:['Посёлок','Город','Крупный город'][i]})]},i))}),z.jsx('b',{className:'formula-arrow','data-viz':'arrow',children:'→'}),z.jsxs('div',{className:'formula-total','data-viz':'total',children:[z.jsx('strong',{children:'Iₘ'}),z.jsx('small',{children:'с учётом населения'})]})]});
  if(index===2)return z.jsxs('div',{className:'formula-service',children:[z.jsx('div',{className:'formula-dots',children:Array.from({length:10},(_,i)=>z.jsx('i',{'data-viz':'dot',className:i<7?'is-reached':''},i))}),z.jsxs('p',{children:[z.jsx('strong',{'data-viz':'total',children:'70%'}),' · пример: 7 из 10 в пределах порога']})]});
  return z.jsxs('div',{className:'formula-capacity',children:[z.jsxs('div',{children:[z.jsx('span',{'data-viz':'bar'}),z.jsx('span',{'data-viz':'lane',className:'formula-closed'}),z.jsx('small',{children:'2 полосы → 1'})]}),z.jsx('b',{className:'formula-arrow',children:'→'}),z.jsxs('div',{'data-viz':'total',children:[z.jsx('strong',{children:'q/C ↑'}),z.jsx('small',{children:'нагрузка выше · поездка дольше'})]})]});
}
function FormulaEquation({index}){
  if(index===0)return z.jsxs('strong',{className:'formula-equation',children:['Aᵢ = Σⱼ Pⱼ · 2',z.jsx('sup',{children:'−tᵢⱼ / 2'})]});
  if(index===1)return z.jsxs('strong',{className:'formula-equation',children:['Iₘ = ',z.jsxs('span',{className:'formula-fraction',children:[z.jsx('span',{children:'100 · Σᵢ pᵢAᵢ'}),z.jsx('span',{children:'B · Σᵢ pᵢ'})]})]});
  if(index===2)return z.jsxs('strong',{className:'formula-equation',children:['Sₖ(τ) = ',z.jsxs('span',{className:'formula-fraction',children:[z.jsx('span',{children:'100 · Σᵢ wᵢ · 1[dᵢₖ ≤ τ]'}),z.jsx('span',{children:'Σᵢ wᵢ'})]})]});
  return z.jsxs('strong',{className:'formula-equation formula-equation-compact',children:[z.jsx('span',{children:'C = 1 800 · n'}),z.jsx('span',{children:'t = t₀ · [1 + 0,15(q/C)⁴]'})]});
}
demoFormula.Component=()=>z.jsx('div',{className:'formula-board',children:formulaRows.map(([title,formula,note],index)=>z.jsxs('article',{'data-part':'formula-card',children:[z.jsxs('header',{children:[z.jsx('span',{children:String(index+1).padStart(2,'0')}),z.jsx('h2',{children:title})]}),z.jsx(FormulaVisual,{index}),z.jsxs('div',{'data-part':'formula-detail',children:[z.jsx(FormulaEquation,{index}),z.jsx('p',{children:note})]})]},title))});
demoFormula.beats[0].run=async function(c){
  const cards=c.parts('formula-card');
  for(const card of cards){
    c.run.animate(card,Sj,{dur:.7});
    c.run.all([...card.querySelectorAll('[data-viz="bar"]')],[{transform:'scaleX(0)'},{transform:'scaleX(1)'}],{dur:.8,stagger:.18,delay:.2});
    c.run.all([...card.querySelectorAll('[data-viz="dot"]')],[{opacity:0,transform:'scale(.5)'},{opacity:1,transform:'scale(1)'}],{dur:.45,stagger:.09,delay:.2});
    c.run.all([...card.querySelectorAll('[data-viz="arrow"],[data-viz="total"]')],Sj,{dur:.6,delay:.65});
    c.run.animate(card.querySelector('[data-viz="lane"]'),[{opacity:1},{opacity:.25}],{dur:.8,delay:.7});
    c.run.animate(card.querySelector('[data-part="formula-detail"]'),Sj,{dur:.7,delay:.7});
    await c.run.sleep(1.65);
  }
};
