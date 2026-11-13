const fs=require('fs');const n=parseInt(fs.readFileSync(0,'utf8').trim(),10);
if(n<2){console.log(0);process.exit(0);}
const m=(n+1)>>1,s=new Uint8Array(m).fill(1),r=Math.floor(Math.sqrt(n));
for(let i=3;i<=r;i+=2)if(s[i>>1])for(let j=i*i;j<=n;j+=2*i)s[j>>1]=0;
let c=1;for(let i=3;i<=n;i+=2)if(s[i>>1])c++;console.log(c);
