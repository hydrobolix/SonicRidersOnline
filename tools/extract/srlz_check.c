/* Round-trip check for the 0x80000001 container (N = 1).
 * Decodes a raw container file, re-encodes the result with the disc compressor's
 * rules and compares with the input.
 *   exit 0  identical, exact-size rules
 *   exit 10 identical when matching may read ONE byte past the end (value 0)
 *   other   decode error or mismatch
 * Build: gcc -O2 -o srlz_check srlz_check.c ; use: srlz_check file.raw
 * Rules (verified on all 1,562 container files of the US disc): greedy; at each
 * position take the longest match in the 255-byte window; accept if length >= 2;
 * ties go to the FARTHEST offset; otherwise emit a literal. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static uint8_t *out; static size_t on; static int bitn; static uint8_t cur;
static void bit(int b){ cur=(uint8_t)((cur<<1)|b); if(++bitn==8){ out[on++]=cur; bitn=0; cur=0; } }
static void byte(uint8_t v){ for(int i=7;i>=0;i--) bit((v>>i)&1); }

int main(int argc, char **argv){
  if(argc<2) return 1;
  FILE *f=fopen(argv[1],"rb"); if(!f) return 1;
  fseek(f,0,SEEK_END); size_t fn=(size_t)ftell(f); fseek(f,0,SEEK_SET);
  uint8_t *in=calloc(fn+4,1); if(fread(in,1,fn,f)!=fn) return 9; fclose(f);
  if(in[0]!=0x80||in[1]||in[2]||in[3]!=1) return 2;
  size_t n=(size_t)in[4]<<24|(size_t)in[5]<<16|(size_t)in[6]<<8|in[7];
  uint8_t *d=calloc(n+512,1); size_t dn=0, p=0; int left=8; const uint8_t *s=in+0x20;
  #define RD() ({ uint8_t _b=(uint8_t)(((s[p]<<(8-left))&0xff)|(left<8?(s[p+1]>>left):0)); p++; _b; })
  while(dn<n){
    left--; int b=(s[p]>>left)&1; if(left==0){ left=8; p++; }
    if(!b) d[dn++]=RD();
    else { size_t off=RD(), ln=RD(); if(!off||off>dn) return 3; while(ln--){ d[dn]=d[dn-off]; dn++; } }
    if(p>fn) return 4;
  }
  for(int mode=0; mode<2; mode++){
    out=calloc(n*2+64,1); on=0x20; bitn=0; cur=0; memcpy(out,in,8);
    size_t i=0, lim=n+mode;               /* mode 1: one virtual zero byte after the data */
    while(i<n){
      int bl=0, bo=0; size_t maxo=i<255?i:255;
      for(size_t off=1; off<=maxo; off++){
        int l=0; while(i+l<lim && l<255 && d[i+l-off]==d[i+l]) l++;
        if(l>=bl && l>0){ bl=l; bo=(int)off; }
      }
      if(bl>=2){ bit(1); byte((uint8_t)bo); byte((uint8_t)bl); i+=bl; } else { bit(0); byte(d[i]); i++; }
    }
    while(bitn) bit(0);
    int same = on<=fn && !memcmp(out,in,on);
    for(size_t k=on; same && k<fn; k++) if(in[k]) same=0;
    free(out);
    if(same) return mode? 10 : 0;
  }
  return 7;
}
