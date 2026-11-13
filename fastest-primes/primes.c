#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
int main(void){long n;if(scanf("%ld",&n)!=1)return 1;if(n<2){puts("0");return 0;}
long m=(n+1)/2;unsigned char*s=malloc(m);memset(s,1,m);long r=sqrt((double)n);
for(long i=3;i<=r;i+=2)if(s[i/2])for(long j=i*i;j<=n;j+=2*i)s[j/2]=0;
long c=1;for(long i=3;i<=n;i+=2)if(s[i/2])c++;printf("%ld\n",c);return 0;}
