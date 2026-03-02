/* Simple notification helper using browser alerts as fallback */
export function notifySuccess(msg) { console.log('SUCCESS:', msg); alert(msg); }
export function notifyError(msg) { console.error('ERROR:', msg); alert(msg); }
