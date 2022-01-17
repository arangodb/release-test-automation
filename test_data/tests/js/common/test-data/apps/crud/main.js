'use strict';

module.context.use('/xxx', require('./routes/xxx'), 'xxx');
module.context.use('/yyyy', require('./routes/yyyy'), 'yyyy');
module.context.use('/logtest', require('./routes/logtest'), 'logtest');

