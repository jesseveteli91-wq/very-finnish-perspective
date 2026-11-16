"""Generate ElevenLabs narration and alignment. Never retry ambiguous paid requests."""
import argparse, base64, hashlib, json, os, re, subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def chunks(text, limit=3500):
    out=[]; current=''
    for paragraph in text.split('\n\n'):
        for sentence in re.split(r'(?<=[.!?])\s+', paragraph.strip()):
            if not sentence: continue
            if len(sentence)>limit: raise ValueError('Sentence exceeds request limit')
            if current and len(current)+len(sentence)+1>limit:
                out.append(current); current=''
            current=(current+' '+sentence).strip()
    if current: out.append(current)
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument('script'); p.add_argument('--output',default='output')
    p.add_argument('--dry-run',action='store_true')
    args=p.parse_args()
    source=Path(args.script).resolve()
    if not source.is_relative_to(Path('scripts/episodes').resolve()) or source.suffix!='.txt':
        raise SystemExit('Script must be scripts/episodes/*.txt')
    text=source.read_text().strip()
    if not text or len(text)>30000: raise SystemExit('Script must contain 1–30000 characters')
    parts=chunks(text)
    if args.dry_run:
        print(json.dumps({'characters':len(text),'parts':len(parts)})); return
    key=os.environ.get('ELEVENLABS_API_KEY','').strip()
    voice=os.environ.get('ELEVENLABS_VOICE_ID','').strip()
    if not key or not voice: raise SystemExit('Missing ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',voice): raise SystemExit('Invalid voice ID format')
    out=Path(args.output)/source.stem; out.mkdir(parents=True,exist_ok=True)
    manifest={'script':str(source.name),'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
              'model':'eleven_multilingual_v2','parts':[]}
    for i,part in enumerate(parts):
        target=out/f'part-{i:03}.mp3'
        if target.exists(): raise SystemExit('Output exists; inspect existing generation before spending again')
        payload={'text':part,'model_id':manifest['model']}
        if i: payload['previous_text']=parts[i-1][-1000:]
        if i+1<len(parts): payload['next_text']=parts[i+1][:1000]
        req=Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps',
                    data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=180) as r: data=json.load(r)
        except HTTPError as e:
            raise SystemExit(f'ElevenLabs HTTP {e.code}. No automatic retry; inspect account permissions/quota.')
        except (URLError,TimeoutError):
            raise SystemExit('Generation outcome uncertain. Check ElevenLabs history before retrying.')
        audio=base64.b64decode(data['audio_base64'],validate=True)
        if len(audio)<1000: raise SystemExit('Audio response too small')
        target.write_bytes(audio)
        alignment=data.get('normalized_alignment') or data.get('alignment')
        if not alignment: raise SystemExit('Audio saved but alignment missing')
        (out/f'part-{i:03}.alignment.json').write_text(json.dumps(alignment))
        (out/f'part-{i:03}.txt').write_text(part)
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(target)]))
        manifest['parts'].append({'file':target.name,'duration':duration,'characters':len(part)})
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
        print(f'Part {i+1}/{len(parts)} generated: {duration:.2f}s')
    (out/'concat.txt').write_text(''.join("file '"+x['file']+"'\n" for x in manifest['parts']))
    subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(out/'concat.txt'),
                    '-c:a','libmp3lame','-b:a','128k',str(out/'narration.mp3')],check=True)
    subprocess.run(['ffmpeg','-v','error','-i',str(out/'narration.mp3'),'-f','null','-'],check=True)
    print('Narration and per-part alignment verified. This workflow does not publish videos.')

if __name__=='__main__': main()
