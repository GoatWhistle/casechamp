import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'Атлас связности — транспорт и территории',description:'Интерактивная карта транспортных связей России. Маршруты, сезонность и индексы доступности.',icons:{icon:'/favicon.svg'}};
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="ru"><body>{children}</body></html>}
