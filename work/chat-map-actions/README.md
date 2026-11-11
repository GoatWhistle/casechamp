# Контекстные кнопки карты

2026-11-11, feat/map-first-ui HEADcdb2c2e. Предыдущая правка затронула mapCommands,
но кнопка из ChatCalculationRun оставалась отдельной строкой. Теперь кнопки каждого
CorridorCalculation размещаются в общей строке с действиями. Подпись берётся из
corridor.road_ref: «М-10 на карте»; title объясняет приближение/выделение на основной карте.
Каждой кнопке передаётся её calculation, вместо прежнего выбора calculations[0].
Кнопки stress остаются внутри подписанного блока конкретного перекрытия.

Проверено npm run verify:479tests,36rules,types,lint,build. Browser1440 с региональным
расчётом: errors=[], aligned=true (центры кнопок в одной строке), expanded=true.
Снимок desktop.png. Прежнее предупреждение о больших chunks. Без model calls/commit/push.
