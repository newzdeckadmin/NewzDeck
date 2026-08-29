from __future__ import annotations

import email.utils
import contextlib
import html
import hashlib
import json
import os
import queue
import copy
import re
import secrets
import shutil
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from pathlib import Path
from typing import Any, Callable

VIDEO_EXTS = {'.mkv','.mp4','.m4v','.avi','.mov','.wmv','.ts','.m2ts','.webm','.mpg','.mpeg'}

def _friendly_grab_exception(exc: Exception) -> str:
    text=str(exc or '').strip(); low=text.casefold()
    if any(x in low for x in ('winerror 10054','errno 10054','forcibly closed','connection reset','connection aborted','broken pipe','remote end closed')):
        return ('The built-in download engine briefly reset its local connection while queueing this release. '
                'Check Downloads; if the release is not listed, try Grab again in a moment.')
    if any(x in low for x in ('winerror 10061','errno 10061','connection refused','timed out','timeout','no connection could be made because the target machine actively refused it')):
        return ('The built-in download engine was temporarily unavailable while queueing this release. '
                'Check Downloads; if it is not listed, try Grab again in a moment.')
    return text or 'The release could not be queued.'

class ReleaseFetchError(RuntimeError):
    """A release-specific Newznab NZB retrieval failure.

    ``blacklist`` is deliberately separate from the exception text: authentication,
    DNS, or broad indexer outages should be reported without poisoning a release,
    while repeated remote resets/404s for a result that was just returned by search
    are strong evidence that the exact post is no longer retrievable.
    """
    def __init__(self, message: str, *, blacklist: bool, error_code: str = 'nzb_fetch_failed'):
        super().__init__(message)
        self.blacklist = bool(blacklist)
        self.error_code = str(error_code or 'nzb_fetch_failed')


def _read(path: Path, default):
    try:
        if not path.exists(): return default
        with path.open('r', encoding='utf-8') as f: return json.load(f)
    except Exception: return default

def _write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_name(path.name + f'.{os.getpid()}.{threading.get_ident()}.tmp')
    try:
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
            f.flush()
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def _version_tuple(value: Any) -> tuple[int, ...]:
    nums=[int(x) for x in re.findall(r'\d+',str(value or ''))[:4]]
    return tuple((nums+[0,0,0,0])[:4])

def _date(s: Any) -> str:
    s = str(s or '').strip()
    return s[:10] if re.match(r'^\d{4}-\d{2}-\d{2}', s) else ''

def _norm(s: Any) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', str(s or '').casefold()).strip()

def _slug_match(name: str, title: str, year: int | str | None = None) -> bool:
    """Safely match a media title against a release name.

    Matching is token/phrase based rather than substring based.  This matters for
    short titles such as ``Silo``: the old substring test considered the release
    group ``EPSILON`` a title match because the letters ``silo`` occur inside
    ``epsilon``.  Indexers are allowed to return broad/category matches, so local
    identity validation must never rely on arbitrary substrings.
    """
    release_tokens=_norm(name).split()
    title_tokens=_norm(title).split()
    if not release_tokens or not title_tokens:
        return False

    def contains_sequence(haystack:list[str], needle:list[str]) -> bool:
        width=len(needle)
        return any(haystack[i:i+width]==needle for i in range(0,len(haystack)-width+1))

    matched=contains_sequence(release_tokens,title_tokens)

    # Acrostic/stylized titles such as S.W.A.T. and 9-1-1 are commonly collapsed
    # to one token by release names.  Only use this fallback when the canonical
    # title itself is made entirely of one-character tokens; never collapse a
    # normal word because that would reintroduce substring false positives.
    if not matched and len(title_tokens)>1 and all(len(x)==1 for x in title_tokens):
        compact=''.join(title_tokens)
        matched=compact in release_tokens

    if not matched:
        return False

    y=str(year or '').strip()
    if not y:
        return True
    release_years=re.findall(r'\b(?:19|20)\d{2}\b',str(name or ''))
    return y in release_years or not release_years

def _safe_component(value: Any, fallback: str = 'Media') -> str:
    text = str(value or '').strip()
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip(' .')

    if text.upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:
        text = '_' + text
    return (text or fallback)[:180]

_TV_COUNTRY_TAGS = {
    'US':'US','USA':'US','UNITED STATES':'US','UNITED STATES OF AMERICA':'US',
    'GB':'UK','UK':'UK','GBR':'UK','UNITED KINGDOM':'UK',
    'AU':'AU','AUS':'AU','AUSTRALIA':'AU',
    'CA':'CA','CAN':'CA','CANADA':'CA',
    'NZ':'NZ','NZL':'NZ','NEW ZEALAND':'NZ',
    'ZA':'ZA','ZAF':'ZA','SOUTH AFRICA':'ZA',
    'DE':'DE','DEU':'DE','GERMANY':'DE',
    'FR':'FR','FRA':'FR','FRANCE':'FR',
    'ES':'ES','ESP':'ES','SPAIN':'ES',
    'IT':'IT','ITA':'IT','ITALY':'IT',
    'NL':'NL','NLD':'NL','NETHERLANDS':'NL',
    'SE':'SE','SWE':'SE','SWEDEN':'SE',
    'NO':'NO','NOR':'NO','NORWAY':'NO',
    'DK':'DK','DNK':'DK','DENMARK':'DK',
    'FI':'FI','FIN':'FI','FINLAND':'FI',
    'PL':'PL','POL':'PL','POLAND':'PL',
    'BR':'BR','BRA':'BR','BRAZIL':'BR',
    'MX':'MX','MEX':'MX','MEXICO':'MX',
    'IN':'IN','IND':'IN','INDIA':'IN',
    'JP':'JP','JPN':'JP','JAPAN':'JP',
    'KR':'KR','KOR':'KR','SOUTH KOREA':'KR',
}

def _tv_country_tag(value: Any) -> str:
    raw=str(value or '').strip().upper().replace('_',' ')
    return _TV_COUNTRY_TAGS.get(raw, raw if re.fullmatch(r'[A-Z]{2}',raw) else '')

def _release_tv_country_tag(release_title: Any, title: Any) -> str:
    """Extract a country-edition token such as US/UK/AU from a release title.

    This is an import-time safety net for pre-v3.4.12 library records that have not
    yet received the new TMDB-backed series identity fields.  It intentionally only
    trusts a country token immediately after the canonical series title.
    """
    release_tokens=re.findall(r'[A-Z0-9]+',str(release_title or '').upper())
    title_tokens=re.findall(r'[A-Z0-9]+',str(title or '').upper())
    if not release_tokens or not title_tokens or len(release_tokens)<=len(title_tokens): return ''
    for start in range(0,min(4,max(1,len(release_tokens)-len(title_tokens)+1))):
        if release_tokens[start:start+len(title_tokens)]!=title_tokens: continue
        nxt=release_tokens[start+len(title_tokens)] if start+len(title_tokens)<len(release_tokens) else ''
        tag=_tv_country_tag(nxt)
        if tag: return tag
    return ''

def _episode_token(season: int | None, episode: int | None) -> str:
    try:
        return f'S{int(season):02d}E{int(episode):02d}'
    except Exception:
        return ''

def parse_release(title: str) -> dict[str, Any]:
    raw = str(title or '')
    low = raw.casefold()
    resolution = next((x for x in ('2160p','1080p','720p','576p','480p') if x in low), 'Unknown')
    if 'remux' in low: source = 'Remux'
    elif re.search(r'blu[ ._-]?ray|b[dr]rip|bdremux', low): source = 'BluRay'
    elif re.search(r'web[ ._-]?dl|web-dl|web\.dl', low): source = 'WEB-DL'
    elif 'webrip' in low or 'web rip' in low: source = 'WEBRip'
    elif re.search(r'\b(?:2160p|1080p|720p|576p|480p)\b[ ._-]+web(?:[ ._-]|$)', low) \
            or re.search(r'(?:^|[ ._-])web[ ._-]+(?:h[ ._-]?26[45]|x26[45]|hevc|av1|ddp|eac3|aac)(?:[ ._-]|$)', low): source = 'WEB'
    elif 'hdtv' in low: source = 'HDTV'
    elif 'dvd' in low: source = 'DVD'
    else: source = 'Unknown'
    if re.search(r'\b(?:x265|h[ ._-]?265|hevc)\b', low): codec = 'HEVC/x265'
    elif re.search(r'\b(?:x264|h[ ._-]?264|avc)\b', low): codec = 'AVC/x264'
    elif re.search(r'\bav1\b', low): codec = 'AV1'
    else: codec = 'Unknown'
    if re.search(r'\b(?:dolby[ ._-]?vision|dovi|dv)\b', low): hdr = 'Dolby Vision'
    elif re.search(r'hdr10\+', low): hdr = 'HDR10+'
    elif re.search(r'\bhdr10\b', low): hdr = 'HDR10'
    elif re.search(r'\bhdr\b', low): hdr = 'HDR'
    else: hdr = 'SDR/Unknown'
    if 'atmos' in low: audio = 'Atmos'
    elif 'truehd' in low: audio = 'TrueHD'
    elif re.search(r'dts[ ._-]?hd|dts-hd', low): audio = 'DTS-HD'
    elif re.search(r'eac3|ddp|dd\+', low): audio = 'DD+'
    elif re.search(r'\baac\b', low): audio = 'AAC'
    else: audio = 'Unknown'
    grp = ''
    m = re.search(r'-([A-Za-z0-9][A-Za-z0-9._]{1,30})$', raw)
    if m: grp = m.group(1)

    sm = re.search(r'\bS(\d{1,2})E(\d{1,3})(?P<tail>(?:E\d{1,3})*)\b', raw, re.I)
    season = int(sm.group(1)) if sm else None
    episode_numbers: list[int] = []
    if sm:
        episode_numbers.append(int(sm.group(2)))
        episode_numbers.extend(int(x) for x in re.findall(r'E(\d{1,3})', sm.group('tail') or '', re.I))
    if not sm:
        xm = re.search(r'\b(\d{1,2})x(\d{1,3})(?:[ ._-]*(?:and|&|x)[ ._-]*(\d{1,3}))?\b', raw, re.I)
        if xm:
            season=int(xm.group(1)); episode_numbers=[int(xm.group(2))]
            if xm.group(3): episode_numbers.append(int(xm.group(3)))
    if season is None:
        only = re.search(r'\bS(\d{1,2})(?!E\d)\b', raw, re.I)
        if only: season=int(only.group(1))
        else:
            named = re.search(r'(?i)\bseason[ ._-]*(\d{1,2})\b', raw)
            if named: season=int(named.group(1))
    episode = episode_numbers[0] if episode_numbers else None
    is_multi_episode = len(set(episode_numbers)) > 1
    pack_marker = bool(re.search(r'(?i)(?:complete[ ._-]*(?:season|series)|season[ ._-]*\d{1,2}[ ._-]*(?:pack|complete)|(?:pack|complete)[ ._-]*S\d{1,2})', raw))
    is_season_pack = bool(season is not None and episode is None and (pack_marker or re.search(r'\bS\d{1,2}\b', raw, re.I)))
    quality = f'{resolution} {source}' if resolution != 'Unknown' or source != 'Unknown' else 'Unknown'
    return {
        'quality': quality, 'resolution':resolution, 'source':source, 'codec':codec,
        'hdr':hdr, 'audio':audio, 'release_group':grp, 'season':season,
        'episode':episode, 'episode_numbers':sorted(set(episode_numbers)),
        'is_multi_episode':is_multi_episode, 'is_season_pack':is_season_pack,
    }

SMART_IMPORT_SOURCES = {"automation_grab", "manual_media_grab"}

def _is_smart_import_context(context: dict[str, Any] | None) -> bool:
    return isinstance(context, dict) and str(context.get("source") or "") in SMART_IMPORT_SOURCES

INDEXER_PRIMARY_TIMEOUT = 7.0
INDEXER_FALLBACK_TIMEOUT = 7.0
INDEXER_SEARCH_MARGIN = 2.0

def _indexer_search_wall_timeout() -> float:
    """Maximum wall-clock budget for one indexer search worker.

    Keep this derived from the two sequential request budgets so the outer
    ThreadPool wait can never cancel a healthy generic fallback before it has
    had a chance to finish.
    """
    return INDEXER_PRIMARY_TIMEOUT + INDEXER_FALLBACK_TIMEOUT + INDEXER_SEARCH_MARGIN

DEFAULT_PROFILES = [
    {
        'id':'quality-4k-preferred','name':'4K Preferred','qualities':['2160p Remux','2160p BluRay','2160p WEB-DL','2160p WEBRip','1080p Remux','1080p BluRay','1080p WEB-DL','1080p WEBRip','720p WEB-DL','720p HDTV'],
        'cutoff':'2160p WEB-DL','min_size_mb':0,'max_size_gb':0,'reject_terms':['cam','telesync','password','encrypted'],'preferred_groups':[],'custom_formats':[{'name':'HEVC / x265','contains':['x265','hevc'],'score':25},{'name':'Dolby Vision','contains':['dolby vision','dovi',' dv '],'score':20},{'name':'HDR','contains':['hdr'],'score':10},{'name':'Atmos','contains':['atmos'],'score':10}],
    },
    {
        'id':'quality-1080p','name':'1080p Balanced','qualities':['1080p Remux','1080p BluRay','1080p WEB-DL','1080p WEBRip','1080p HDTV','720p WEB-DL','720p HDTV'],
        'cutoff':'1080p WEB-DL','min_size_mb':0,'max_size_gb':0,'reject_terms':['cam','telesync','password','encrypted'],'preferred_groups':[],'custom_formats':[{'name':'HEVC / x265','contains':['x265','hevc'],'score':20},{'name':'Atmos','contains':['atmos'],'score':10}],
    },
]

class MediaAutomationEngine:
    def __init__(self, data_dir: Path, protect_secret: Callable[[str], str], unprotect_secret: Callable[[str], str], download_manager, get_providers: Callable[[], list[dict[str,Any]]], version='3.6.6'):
        self.data_dir = Path(data_dir)
        self.library_file = self.data_dir / 'media-library.json'
        self.config_file = self.data_dir / 'media-automation-config.json'
        self.indexers_file = self.data_dir / 'indexers.json'
        self.profiles_file = self.data_dir / 'quality-profiles.json'
        self.activity_file = self.data_dir / 'automation-activity.json'
        self.metadata_cache_file = self.data_dir / 'metadata-cache.json'
        self.metadata_cloud_state_file = self.data_dir / 'metadata-cloud-state.json'
        self.discover_state_file = self.data_dir / 'discover-state.json'
        self.automation_runtime_file = self.data_dir / 'automation-runtime.json'
        self.media_quality_cache_file = self.data_dir / 'media-quality-cache.json'
        self.grab_reservation_dir = self.data_dir / 'automation-grab-reservations'
        self.automation_cycle_lock_file = self.data_dir / '.automation-cycle.lock'
        self.protect_secret = protect_secret
        self.unprotect_secret = unprotect_secret
        self.download_manager = download_manager
        self.get_providers = get_providers
        self.version = version
        self.lock = threading.RLock()
        self.auto_run_lock = threading.Lock()
        self.auto_thread = None
        self.reconcile_lock = threading.Lock()
        self.reconcile_thread = None
        self.release_feed_cache: list[dict[str,Any]] = []
        self.release_feed_cache_ts = 0.0
        self.metadata_circuit_lock = threading.RLock()
        self.metadata_state_lock = threading.RLock()
        self.metadata_cache_lock = threading.RLock()
        self.activity_lock = threading.RLock()
        self.discover_home_cache_lock = threading.RLock()
        self.discover_home_cache: dict[str,Any]|None = None
        self.discover_home_cache_ts = 0.0
        # Title detail responses are relatively expensive (cast, crew, video,
        # recommendations and similar titles). Keep the raw TMDB aggregate warm for
        # a short window and re-decorate library state on every request.
        self.discover_detail_cache_lock = threading.RLock()
        self.discover_detail_cache: dict[str, tuple[float, dict[str,Any]]] = {}
        # Discover uses stale-while-revalidate rather than making the UI wait on a
        # cold/slow TMDB aggregate every time the Home or For You tab is opened.
        # Refresh work is single-flight inside this process and additionally guarded
        # by a tiny cross-process lock so the desktop + service do not stampede the
        # hosted Metadata Service together.
        self.discover_home_refresh_lock = threading.Lock()
        self.discover_home_refreshing = False
        self.discover_for_you_cache_lock = threading.RLock()
        self.discover_for_you_cache: list[dict[str,Any]]|None = None
        self.discover_for_you_cache_ts = 0.0
        self.discover_for_you_cache_signature = ''
        self.discover_for_you_refresh_lock = threading.Lock()
        self.discover_for_you_refreshing = False
        self.metadata_circuit_open_until = 0.0
        self.metadata_circuit_reason = ''
        # Config, indexer, and profile files are read very frequently but change
        # rarely. Keep an mtime-aware in-memory snapshot so normal Automation and
        # Discover traffic does not repeatedly parse the same JSON from disk.
        self._small_json_cache_lock = threading.RLock()
        self._small_json_cache: dict[str, tuple[int, Any]] = {}

        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def _read_small_cached(self, path: Path, default):
        try:
            mtime_ns = int(path.stat().st_mtime_ns)
        except OSError:
            mtime_ns = -1
        key = str(path)
        with self._small_json_cache_lock:
            cached = self._small_json_cache.get(key)
            if cached is None or cached[0] != mtime_ns:
                value = _read(path, default)
                self._small_json_cache[key] = (mtime_ns, value)
            else:
                value = cached[1]
            # Callers intentionally mutate returned settings/profile records.
            # Keep the cached snapshot isolated from those edits.
            return copy.deepcopy(value)

    def _library(self):
        x=_read(self.library_file,[])
        if not isinstance(x,list): return []
        # v3.5.15: Automatic TV library naming means the canonical series title,
        # not the historical ``Title (Year)`` convention.  Normalize persisted
        # automatic values on read so existing libraries (for example
        # ``Silo (2023)``) immediately produce ``Silo`` for future imports while
        # preserving explicit/manual names and country disambiguation.
        changed=False
        for item in x:
            if not isinstance(item,dict) or item.get('kind')!='tv': continue
            source=str(item.get('library_title_source') or '').lower()
            if source=='manual': continue
            current=str(item.get('library_title') or '').strip()
            title=str(item.get('title') or 'TV Show').strip() or 'TV Show'
            year=str(item.get('year') or '').strip()
            # Very old records may predate library_title_source. Preserve a
            # nonstandard/custom value as a manual override instead of silently
            # replacing it during migration.
            if not source and current and current not in {title, f'{title} ({year})' if year else title}:
                item['library_title_source']='manual'; changed=True; continue
            desired=self._tv_default_library_title(item)
            if current!=desired or source!='auto':
                item['library_title']=desired; item['library_title_source']='auto'; changed=True
        if changed: _write(self.library_file,x)
        return x
    def _save_library(self,x): _write(self.library_file,x)
    def _profiles(self):
        x=self._read_small_cached(self.profiles_file,DEFAULT_PROFILES); return x if isinstance(x,list) and x else copy.deepcopy(DEFAULT_PROFILES)
    def _indexers(self):
        x=self._read_small_cached(self.indexers_file,[]); return x if isinstance(x,list) else []
    def _config(self):
        x=self._read_small_cached(self.config_file,{})
        x=x if isinstance(x,dict) else {}

        changed=False
        for plural,singular in (('tv_roots','tv_root'),('movie_roots','movie_root')):
            roots=x.get(plural)
            if not isinstance(roots,list):
                roots=[]
            legacy=str(x.get(singular) or '').strip()
            if legacy and not any(str(v or '').strip().casefold()==legacy.casefold() for v in roots):
                roots=[legacy]+roots
            cleaned=[]; seen=set()
            for value in roots:
                path=str(value or '').strip()
                key=path.casefold()
                if path and key not in seen:
                    cleaned.append(path); seen.add(key)
            if x.get(plural)!=cleaned:
                x[plural]=cleaned[:20]; changed=True
            if singular in x:
                x.pop(singular,None); changed=True


        if 'automatic_queue_depth' not in x:
            x['automatic_queue_depth']=25; changed=True


        env_metadata=str(os.environ.get('NEWZDECK_METADATA_URL') or '').strip().rstrip('/')
        current_metadata=str(x.get('metadata_service_url') or '').strip().rstrip('/')
        if env_metadata:
            if current_metadata != env_metadata:
                x['metadata_service_url']=env_metadata; changed=True
        elif not current_metadata or current_metadata in {'http://127.0.0.1:8400','http://localhost:8400'}:
            x['metadata_service_url']='https://api.newzdeck.com'; changed=True

        if not str(x.get('metadata_installation_id') or '').strip():
            x['metadata_installation_id']='install_'+secrets.token_hex(16); changed=True
        if not str(x.get('metadata_installation_secret_protected') or '').strip():
            try:
                x['metadata_installation_secret_protected']=self.protect_secret(secrets.token_urlsafe(40)); changed=True
            except Exception:
                pass


        if 'automatic_library_scan_minutes' not in x:
            x['automatic_library_scan_minutes']=30; changed=True
        if 'automatic_storage_reserve_gb' not in x:
            x['automatic_storage_reserve_gb']=5; changed=True
        if 'automatic_season_packs_enabled' not in x:
            x['automatic_season_packs_enabled']=True; changed=True
        continuous_defaults={
            'automatic_feed_enabled':True,
            'automatic_feed_interval_minutes':5,
            'automatic_smart_retry_enabled':True,
            'automatic_quiet_hours_enabled':False,
            'automatic_quiet_start':'01:00',
            'automatic_quiet_end':'07:00',
            'automatic_notifications_enabled':False,
        }
        for key,value in continuous_defaults.items():
            if key not in x:
                x[key]=value; changed=True
        if str(x.get('automatic_movie_availability') or '') not in {'digital_physical','theatrical'}:
            x['automatic_movie_availability']='digital_physical'; changed=True

        if str(x.get('tv_season_template') or '').strip() == 'Season {season:02d}':
            x['tv_season_template']='Season {season}'; changed=True
        old_tv_folder=str(x.get('tv_folder_template') or '').strip()
        old_tv_file=str(x.get('tv_file_template') or '').strip()
        if not old_tv_folder or old_tv_folder == '{title} ({year})':
            if old_tv_folder != '{library_title}': x['tv_folder_template']='{library_title}'; changed=True
        if not old_tv_file or old_tv_file == '{title} ({year}) - {episode_token} - {episode_title}':
            if old_tv_file != '{library_title} - {episode_token} - {episode_title}': x['tv_file_template']='{library_title} - {episode_token} - {episode_title}'; changed=True
        if changed:
            _write(self.config_file,x)
        return x
    def _activity(self):
        x=_read(self.activity_file,[]); return x if isinstance(x,list) else []
    def _event(self, kind:str, message:str, **details):
        with self.activity_lock:
            items=self._activity(); items.insert(0,{'ts':time.time(),'kind':kind,'message':message,'details':details}); _write(self.activity_file,items[:300])

    def _auto_runtime(self):
        x=_read(self.automation_runtime_file,{})
        if not isinstance(x,dict): x={}
        if not isinstance(x.get('targets'),dict): x['targets']={}
        return x

    def _save_auto_runtime(self, value):
        if not isinstance(value,dict): value={}
        targets=value.get('targets') if isinstance(value.get('targets'),dict) else {}
        cutoff=time.time()-(45*86400)
        cleaned={}
        for key,rec in targets.items():
            if not isinstance(rec,dict): continue
            stamp=max(float(rec.get('last_search_ts') or 0),float(rec.get('last_grab_ts') or 0),float(rec.get('updated_ts') or 0))
            if stamp<=0 or stamp>=cutoff: cleaned[str(key)]=rec
        value['targets']=cleaned
        _write(self.automation_runtime_file,value)

    def _iso_epoch(self, value: Any) -> float:
        text=str(value or '').strip()
        if not text: return 0.0
        try:
            dt=datetime.fromisoformat(text.replace('Z','+00:00'))
            if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            return 0.0

    def _auto_target_key(self, row:dict[str,Any]|None=None, context:dict[str,Any]|None=None) -> str:
        src=context if isinstance(context,dict) else row if isinstance(row,dict) else {}
        item_id=str(src.get('item_id') or '').strip()
        if not item_id: return ''
        kind=str(src.get('kind') or '')
        season=src.get('season'); episode=src.get('episode')
        season_pack=bool(src.get('season_pack')) or (kind=='tv' and season is not None and episode is None)
        if season_pack:
            try: return f"tv:{item_id}:s{int(season):02d}:pack"
            except Exception: return f'tv:{item_id}:pack'
        if kind=='tv' or season is not None or episode is not None:
            try: return f"tv:{item_id}:s{int(season):02d}e{int(episode):03d}"
            except Exception: return f'tv:{item_id}'
        return f'movie:{item_id}'

    def recover_download_context(self, collection_id: str, release_title: str = '') -> dict[str,Any]:
        """Rebuild Automation context for a SAB job submitted by another runtime.

        The shared SAB engine can outlive/reconnect across desktop/service handoffs.
        automation-runtime.json keeps enough target/collection metadata to recover
        the library destination and episode identity when one process did not have
        the in-memory tracking record yet.
        """
        cid=str(collection_id or '').strip()
        title=str(release_title or '').strip()
        rt=self._auto_runtime()
        targets=rt.get('targets') if isinstance(rt.get('targets'),dict) else {}
        matches=[]
        for key,rec in targets.items():
            if not isinstance(rec,dict): continue
            score=0
            if cid and str(rec.get('last_collection_id') or '')==cid: score+=1000
            if title and _norm(rec.get('last_grab_title')) and _norm(rec.get('last_grab_title'))==_norm(title): score+=100
            if score<=0: continue
            matches.append((score,float(rec.get('last_grab_ts') or rec.get('updated_ts') or 0),str(key),rec))
        if not matches:
            # v3.5.15: recover older/manual Automation grabs even when the
            # automation-runtime target record was lost by a stale desktop/service
            # writer. Only accept an unambiguous TV title + SxxEyy match so Smart
            # Import never guesses a library destination.
            parsed_title=parse_release(title) if title else {}
            sn=parsed_title.get('season'); en=parsed_title.get('episode')
            fallback=[]
            if sn is not None and en is not None and not bool(parsed_title.get('is_multi_episode')):
                for candidate in self._library():
                    if not isinstance(candidate,dict) or str(candidate.get('kind') or '')!='tv':
                        continue
                    if not _slug_match(title,str(candidate.get('title') or '')):
                        continue
                    sr=next((x for x in candidate.get('seasons',[]) if int(x.get('season_number',0) or 0)==int(sn)),None)
                    ep=next((x for x in (sr or {}).get('episodes',[]) if int(x.get('episode_number',0) or 0)==int(en)),None)
                    if ep is not None:
                        fallback.append(candidate)
            if len(fallback)!=1:
                return {}
            item_id=str(fallback[0].get('id') or '')
            if not item_id:
                return {}
            key=self._auto_target_key(context={'item_id':item_id,'kind':'tv','season':int(sn),'episode':int(en),'season_pack':False})
            rec={'last_grab_title':title,'last_grab_ts':time.time()}
        else:
            _,_,key,rec=max(matches,key=lambda x:(x[0],x[1]))
        kind='movie'; item_id=''; season=None; episode=None; season_pack=False
        m=re.fullmatch(r'tv:([^:]+):s(\d{1,2})e(\d{1,3})',key,re.I)
        if m:
            kind='tv'; item_id=m.group(1); season=int(m.group(2)); episode=int(m.group(3))
        else:
            m=re.fullmatch(r'tv:([^:]+):s(\d{1,2}):pack',key,re.I)
            if m:
                kind='tv'; item_id=m.group(1); season=int(m.group(2)); season_pack=True
            else:
                m=re.fullmatch(r'movie:([^:]+)',key,re.I)
                if m: item_id=m.group(1)
                else: return {}
        item=next((x for x in self._library() if str(x.get('id') or '')==item_id),None)
        if not item:
            return {}
        root=self._resolve_root(item)
        episode_title=''
        pack_episode_numbers=[]
        if kind=='tv' and season is not None:
            sr=next((x for x in item.get('seasons',[]) if int(x.get('season_number',0) or 0)==int(season)),None)
            if episode is not None:
                ep=next((x for x in (sr or {}).get('episodes',[]) if int(x.get('episode_number',0) or 0)==int(episode)),None)
                episode_title=str((ep or {}).get('name') or '')
            elif season_pack:
                today=datetime.now().date().isoformat()
                pack_episode_numbers=[
                    int(ep.get('episode_number') or 0) for ep in (sr or {}).get('episodes',[])
                    if bool(ep.get('monitored',True)) and int(ep.get('episode_number') or 0)>0
                    and str(ep.get('air_date') or '') and str(ep.get('air_date') or '')<=today
                    and not bool(ep.get('has_file'))
                ]
        parsed=parse_release(title)
        return {
            'source':'automation_grab','item_id':item_id,'kind':kind,
            'title':str(item.get('title') or ''),'year':item.get('year'),
            'season':season,'episode':episode,'season_pack':season_pack,
            'pack_episode_numbers':pack_episode_numbers,'pack_known_episode_numbers':[],
            'episode_title':episode_title,'quality_profile_id':str(item.get('quality_profile_id') or ''),
            'release_title':title or str(rec.get('last_grab_title') or ''),
            'release_quality':str(parsed.get('quality') or 'Unknown'),
            'release_group':str(parsed.get('release_group') or ''),
            'indexer':str(rec.get('last_indexer') or ''),
            'release_guid':str(rec.get('last_grab_guid') or ''),
            'release_score':int(rec.get('last_effective_score') or 0),
            'planned_root_folder':str(root or ''),
            'release_size':0,'automatic':True,'auto_type':'missing',
            'target_key':key,'recovered_context':True,
        }

    def _grab_reservation_path(self, target_key: str) -> Path:
        digest=hashlib.sha256(str(target_key or '').encode('utf-8')).hexdigest()[:32]
        return self.grab_reservation_dir / f'{digest}.json'

    def _claim_grab_reservation(self, target_key: str, hold_seconds: float = 45.0) -> tuple[bool,Path,dict[str,Any]]:
        """Short cross-process claim that closes the simultaneous auto-grab race."""
        key=str(target_key or '').strip()
        if not key:
            return True,Path(),{}
        self.grab_reservation_dir.mkdir(parents=True,exist_ok=True)
        path=self._grab_reservation_path(key)
        now=time.time()
        for _ in range(2):
            try:
                fd=os.open(str(path), os.O_CREAT|os.O_EXCL|os.O_WRONLY)
                payload={'target_key':key,'ts':now,'pid':os.getpid(),'collection_id':'','expires_ts':now+hold_seconds}
                with os.fdopen(fd,'w',encoding='utf-8') as f:
                    json.dump(payload,f)
                return True,path,payload
            except FileExistsError:
                existing=_read(path,{})
                expiry=float((existing or {}).get('expires_ts') or 0)
                if expiry<=now:
                    try: path.unlink()
                    except OSError: pass
                    continue
                return False,path,existing if isinstance(existing,dict) else {}
        return False,path,_read(path,{})

    def _finish_grab_reservation(self, path: Path, payload: dict[str,Any], collection_id: str) -> None:
        if not path:
            return
        try:
            value=dict(payload or {})
            value['collection_id']=str(collection_id or '')
            value['ts']=time.time()
            value['expires_ts']=time.time()+45.0
            _write(path,value)
        except Exception:
            pass

    def _release_grab_reservation(self, path: Path) -> None:
        if not path:
            return
        try: path.unlink(missing_ok=True)
        except OSError: pass

    def _auto_active_targets(self) -> set[str]:
        """Reserve a target until its completed download has finished Smart Import."""
        active=set()
        try:
            snap=self.download_manager.snapshot()
        except Exception:
            rt=self._auto_runtime(); now=time.time()
            for key,rec in (rt.get('targets') or {}).items():
                if not isinstance(rec,dict): continue
                status=str(rec.get('status') or ''); last_grab=float(rec.get('last_grab_ts') or 0)
                if status in {'grabbed','queued','downloading','processing','importing'} and last_grab>0 and now-last_grab<12*3600:
                    active.add(str(key))
            return active
        for job in snap.get('jobs') or []:
            if not isinstance(job,dict): continue
            ctx=job.get('automation_context') if isinstance(job.get('automation_context'),dict) else {}
            if str(ctx.get('source') or '')!='automation_grab': continue
            status=str(job.get('status') or ''); post=str(job.get('post_status') or '')
            imported=bool(job.get('imported')); import_status=str(job.get('import_status') or '')
            pending_import=(status=='completed' and not imported)
            if status in {'queued','downloading','retry_wait','cancelling'} or post in {'queued','verifying','repairing','extracting','importing','waiting'} or pending_import or (import_status=='failed' and not imported):
                key=str(ctx.get('target_key') or self._auto_target_key(context=ctx))
                if key: active.add(key)
        return active

    def _auto_download_states(self) -> dict[str,dict[str,Any]]:
        """Return the best live queue/post-processing state for each Automation target.

        Season-pack jobs are mirrored onto their member episode target keys so Wanted
        never looks idle while one pack is already downloading those episodes.
        """
        states={}
        priority={'processing':6,'downloading':5,'retrying':4,'queued':3,'cancelling':2,'waiting':1}
        try: snap=self.download_manager.snapshot()
        except Exception: return states
        for job in snap.get('jobs') or []:
            if not isinstance(job,dict): continue
            ctx=job.get('automation_context') if isinstance(job.get('automation_context'),dict) else {}
            if str(ctx.get('source') or '')!='automation_grab': continue
            key=str(ctx.get('target_key') or self._auto_target_key(context=ctx))
            if not key: continue
            status=str(job.get('status') or ''); post=str(job.get('post_status') or '')
            if post in {'queued','verifying','repairing','extracting','importing','waiting'}:
                mapped='processing'; message={'queued':'Post-processing queued','verifying':'Verifying download','repairing':'Repairing with PAR2','extracting':'Extracting media','importing':'Importing media to library','waiting':'Post-processing waiting'}.get(post,'Processing media')
            elif status=='downloading': mapped='downloading'; message='Downloading'
            elif status=='retry_wait': mapped='retrying'; message=str(job.get('status_detail') or 'Waiting to retry download')
            elif status=='queued': mapped='queued'; message='Queued for download'
            elif status=='cancelling': mapped='cancelling'; message='Cancelling'
            elif status=='completed' and not bool(job.get('imported')):
                mapped='processing'; import_state=str(job.get('import_status') or '')
                if import_state=='failed': message=str(job.get('post_message') or 'Smart Import needs attention')
                elif import_state=='importing': message='Importing media to library'
                elif import_state=='waiting': message=str(job.get('post_message') or 'Waiting for Smart Import retry')
                else: message='Download complete • waiting for Smart Import'
            else: continue
            pct=float(job.get('percent') or job.get('progress_percent') or 0)
            rec={'status':mapped,'message':message,'progress':pct,'updated_ts':time.time(),'collection_id':str(job.get('collection_id') or ''),'season_pack':bool(ctx.get('season_pack'))}
            keys=[key]
            if bool(ctx.get('season_pack')):
                item_id=str(ctx.get('item_id') or '')
                try: sn=int(ctx.get('season') or 0)
                except Exception: sn=0
                for en in ctx.get('pack_episode_numbers') or []:
                    try: keys.append(f'tv:{item_id}:s{sn:02d}e{int(en):03d}')
                    except Exception: pass
            for target_key in keys:
                old=states.get(target_key)
                if old is None or priority.get(mapped,0)>priority.get(str(old.get('status') or ''),0): states[target_key]=rec
        return states

    def _automatic_failure_snapshot(self) -> list[dict[str,Any]]:
        """Detect terminal failures for automatic grabs without treating user cancellations as bad releases."""
        try:
            snap=self.download_manager.snapshot()
        except Exception:
            return []
        collections={str(x.get('id') or ''):x for x in (snap.get('collections') or []) if isinstance(x,dict)}
        grouped={}
        for job in snap.get('jobs') or []:
            if not isinstance(job,dict): continue
            ctx=job.get('automation_context') if isinstance(job.get('automation_context'),dict) else {}
            # Every release chosen from Automation/Interactive Search carries the
            # automation_grab context. Manual grabs need the same failed-release
            # memory as unattended grabs so the next Interactive Search can warn
            # the user and prevent selecting the exact bad post again.
            if str(ctx.get('source') or '')!='automation_grab': continue
            cid=str(job.get('collection_id') or '')
            if not cid: continue
            grouped.setdefault(cid,{'context':ctx,'jobs':[]})['jobs'].append(job)
        failed=[]
        for cid,group in grouped.items():
            pkg=collections.get(cid,{})
            status=str(pkg.get('status') or '')
            post=str(pkg.get('post_status') or '')

            if status=='cancelled': continue
            # A genuine SAB terminal failure means the release/post itself was bad.
            # A completed transfer whose Smart Import later needs attention is NOT
            # a bad release and must remain retryable without blacklisting it.
            # SAB history failures are mapped to status=failed; import failures keep
            # status=completed and expose import_status/post_status separately.
            terminal=status=='failed'
            if not terminal: continue
            jobs=group.get('jobs') or []; ctx=group.get('context') or {}
            reason=str(pkg.get('post_message') or '')
            code=''
            if not reason:
                for job in jobs:
                    if job.get('error_label') or job.get('error'):
                        reason=str(job.get('error_label') or job.get('error') or 'Download failed'); code=str(job.get('error_code') or ''); break
            if not reason:
                health=pkg.get('health') if isinstance(pkg.get('health'),dict) else {}
                reason=str(health.get('label') or 'Download or post-processing failed')
            failed.append({'collection_id':cid,'context':ctx,'reason':reason[:600],'error_code':code[:80], 'status':status,'post_status':post,'automatic':bool(ctx.get('automatic',False))})
        return failed

    def record_release_failure(self, context:dict[str,Any], reason:str, *, error_code:str='', collection_id:str='') -> bool:
        """Persist one bad Automation release immediately when SAB marks it failed.

        This is intentionally release-specific. A manual Interactive Search grab is
        blocked for that target on the next search, while an unattended grab also
        becomes immediately eligible for the next candidate. Import-only failures
        never call this method.
        """
        if not isinstance(context,dict) or str(context.get('source') or '')!='automation_grab': return False
        key=str(context.get('target_key') or self._auto_target_key(context=context))
        if not key: return False
        cid=str(collection_id or '').strip(); now=time.time()
        with self.lock:
            rt=self._auto_runtime(); handled=set(str(x) for x in rt.get('handled_failure_collections') or [])
            if cid and cid in handled: return False
            targets=rt.get('targets') if isinstance(rt.get('targets'),dict) else {}; rt['targets']=targets; rec=targets.setdefault(key,{})
            guid=str(context.get('release_guid') or '').strip(); title=str(context.get('release_title') or 'Unknown release'); indexer=str(context.get('indexer') or '')
            blacklist=[x for x in rec.get('blacklist') or [] if isinstance(x,dict)]
            already=any((guid and str(x.get('guid') or '').casefold()==guid.casefold()) or (not guid and str(x.get('title') or '').casefold()==title.casefold()) for x in blacklist)
            if not already:
                blacklist.append({'guid':guid,'title':title,'indexer':indexer,'reason':str(reason or 'Release failed')[:600],'error_code':str(error_code or '')[:80],'failed_ts':now,'collection_id':cid,'source':'download_failure'})
                rec['blacklist']=blacklist[-40:]
                if bool(context.get('automatic')): self._record_indexer_outcome(rt,indexer,success=False,ts=now)
                self._event('release-blacklisted',f'Blacklisted failed release {title}',item_id=str(context.get('item_id') or ''),target_key=key,release=title,indexer=indexer,reason=str(reason or ''),collection_id=cid)
            if bool(context.get('automatic')):
                rec.update({'status':'retrying','message':'Previous release failed — searching for the next candidate','updated_ts':now,'next_search_ts':0,'last_grab_ts':0})
            else:
                rec.update({'status':'failed','message':'Previous release failed — choose a different release in Interactive Search','updated_ts':now,'last_grab_ts':0})
            if cid: handled.add(cid)
            rt['handled_failure_collections']=list(handled)[-500:]
            self._save_auto_runtime(rt)
        return not already

    def _indexer_penalty(self, rt:dict[str,Any], name:str, now:float|None=None) -> int:
        """Small, decaying penalty so indexers returning bad NZBs are temporarily deprioritized, never disabled."""
        now=float(now or time.time()); key=str(name or '').strip().casefold()
        health=rt.get('indexer_health') if isinstance(rt.get('indexer_health'),dict) else {}
        rec=health.get(key) if isinstance(health.get(key),dict) else {}
        failures=[float(x) for x in rec.get('failures') or [] if now-float(x)<24*3600]
        successes=[float(x) for x in rec.get('successes') or [] if now-float(x)<24*3600]
        return max(0,min(80,len(failures)*18-len(successes)*6))

    def _record_indexer_outcome(self, rt:dict[str,Any], name:str, *, success:bool, ts:float|None=None):
        key=str(name or '').strip().casefold()
        if not key: return
        now=float(ts or time.time()); health=rt.setdefault('indexer_health',{})
        rec=health.setdefault(key,{'name':str(name or ''),'failures':[],'successes':[]})
        rec['name']=str(name or rec.get('name') or '')
        fld='successes' if success else 'failures'
        rec[fld]=([float(x) for x in rec.get(fld) or [] if now-float(x)<7*86400]+[now])[-50:]
        other='failures' if success else 'successes'
        rec[other]=[float(x) for x in rec.get(other) or [] if now-float(x)<7*86400][-50:]
        rec['last_outcome']='success' if success else 'failure'; rec['updated_ts']=now

    def _sync_automatic_failures(self, rt:dict[str,Any]) -> int:
        """Remember terminally failed Automation releases and prevent accidental re-grabs.

        Automatic grabs immediately search the next candidate. Manual Interactive
        Search grabs are marked failed for the target so the next search can explain
        what happened and ask the user to choose a different release.
        """
        now=time.time(); count=0; targets=rt.setdefault('targets',{}); handled=set(str(x) for x in rt.get('handled_failure_collections') or [])
        for failure in self._automatic_failure_snapshot():
            cid=str(failure.get('collection_id') or '')
            if not cid or cid in handled: continue
            ctx=failure.get('context') if isinstance(failure.get('context'),dict) else {}
            key=str(ctx.get('target_key') or self._auto_target_key(context=ctx))
            if not key: handled.add(cid); continue
            rec=targets.setdefault(key,{})
            guid=str(ctx.get('release_guid') or '').strip(); title=str(ctx.get('release_title') or 'Unknown release'); indexer=str(ctx.get('indexer') or '')
            blacklist=[x for x in rec.get('blacklist') or [] if isinstance(x,dict)]
            already=any((guid and str(x.get('guid') or '').casefold()==guid.casefold()) or (not guid and str(x.get('title') or '').casefold()==title.casefold()) for x in blacklist)
            if not already:
                blacklist.append({'guid':guid,'title':title,'indexer':indexer,'reason':str(failure.get('reason') or 'Release failed'),'error_code':str(failure.get('error_code') or ''),'failed_ts':now,'collection_id':cid,'source':'download_failure'})
                rec['blacklist']=blacklist[-40:]; count+=1
                if bool(failure.get('automatic')):
                    self._record_indexer_outcome(rt,indexer,success=False,ts=now)
                self._event('release-blacklisted',f'Blacklisted failed release {title}',item_id=str(ctx.get('item_id') or ''),target_key=key,release=title,indexer=indexer,reason=str(failure.get('reason') or ''),collection_id=cid)
            if bool(failure.get('automatic')):
                rec.update({'status':'retrying','message':'Previous release failed — searching for the next candidate','updated_ts':now,'next_search_ts':0,'last_grab_ts':0})
            else:
                rec.update({'status':'failed','message':'Previous release failed — choose a different release in Interactive Search','updated_ts':now,'last_grab_ts':0})
            handled.add(cid)
        rt['handled_failure_collections']=list(handled)[-500:]
        return count

    def blacklist_release(self, data:dict[str,Any]):
        item_id=str(data.get('item_id') or '').strip(); item=next((x for x in self._library() if str(x.get('id'))==item_id),None)
        if not item: raise ValueError('Library item was not found')
        context={'item_id':item_id,'kind':str(item.get('kind') or ''),'season':data.get('season'),'episode':data.get('episode')}
        key=str(data.get('target_key') or self._auto_target_key(context=context))
        if not key: raise ValueError('Release target could not be identified')
        guid=str(data.get('guid') or data.get('download_url') or '').strip(); title=str(data.get('title') or 'Release').strip(); indexer=str(data.get('indexer') or '').strip()
        rt=self._auto_runtime(); targets=rt.get('targets') if isinstance(rt.get('targets'),dict) else {}; rt['targets']=targets; rec=targets.setdefault(key,{})
        rows=[x for x in rec.get('blacklist') or [] if isinstance(x,dict)]
        if not any((guid and str(x.get('guid') or '').casefold()==guid.casefold()) or str(x.get('title') or '').casefold()==title.casefold() for x in rows):
            rows.append({'guid':guid,'title':title,'indexer':indexer,'reason':str(data.get('reason') or 'Manually rejected'),'error_code':'manual','failed_ts':time.time(),'collection_id':'','source':'manual'})
        rec['blacklist']=rows[-80:]; rec['updated_ts']=time.time(); rec['next_search_ts']=0
        self._save_auto_runtime(rt); self._event('release-blacklisted',f'Manually blacklisted {title}',item_id=item_id,target_key=key,release=title,indexer=indexer,reason='Manually rejected')
        return {'ok':True,'target_key':key,'blacklist_count':len(rec['blacklist'])}

    def clear_release_blacklist(self, target_key:str='', guid:str=''):
        rt=self._auto_runtime(); targets=rt.get('targets') if isinstance(rt.get('targets'),dict) else {}
        changed=0
        keys=[str(target_key)] if str(target_key) else list(targets)
        for key in keys:
            rec=targets.get(key)
            if not isinstance(rec,dict): continue
            old=[x for x in rec.get('blacklist') or [] if isinstance(x,dict)]
            if guid:
                new=[x for x in old if str(x.get('guid') or '').casefold()!=str(guid).casefold()]
            else:
                new=[]
            changed+=len(old)-len(new); rec['blacklist']=new
            attempts=[x for x in rec.get('attempted_releases') or [] if isinstance(x,dict)]
            if guid: attempts=[x for x in attempts if str(x.get('guid') or '').casefold()!=str(guid).casefold()]
            else: attempts=[]
            rec['attempted_releases']=attempts; rec['next_search_ts']=0; rec['last_grab_ts']=0; rec['updated_ts']=time.time()
        self._save_auto_runtime(rt)
        if changed: self._event('blacklist-cleared',f'Removed {changed} release blacklist entr{("y" if changed==1 else "ies")}',target_key=str(target_key or ''),guid=str(guid or ''))
        return {'ok':True,'removed':changed}

    def _clock_minutes(self, value:Any, fallback:str='00:00') -> int:
        text=str(value or fallback).strip()
        m=re.match(r'^(\d{1,2}):(\d{2})$',text)
        if not m: text=fallback; m=re.match(r'^(\d{1,2}):(\d{2})$',text)
        try: return max(0,min(1439,int(m.group(1))*60+int(m.group(2))))
        except Exception: return 0

    def _quiet_hours_state(self, cfg:dict[str,Any]|None=None) -> dict[str,Any]:
        cfg=cfg if isinstance(cfg,dict) else self.public_config()
        enabled=bool(cfg.get('automatic_quiet_hours_enabled'))
        start_text=str(cfg.get('automatic_quiet_start') or '01:00')[:5]
        end_text=str(cfg.get('automatic_quiet_end') or '07:00')[:5]
        if not enabled:
            return {'enabled':False,'active':False,'start':start_text,'end':end_text,'resume_ts':0}
        now=datetime.now().astimezone(); minute=now.hour*60+now.minute
        start=self._clock_minutes(start_text,'01:00'); end=self._clock_minutes(end_text,'07:00')
        if start==end:
            active=True
        elif start<end:
            active=start<=minute<end
        else:
            active=minute>=start or minute<end
        resume=0.0
        if active:
            target=now.replace(hour=end//60,minute=end%60,second=0,microsecond=0)
            if start>=end and minute>=start:
                target+=timedelta(days=1)
            elif target<=now:
                target+=timedelta(days=1)
            resume=target.timestamp()
        return {'enabled':True,'active':active,'start':start_text,'end':end_text,'resume_ts':resume}

    def _human_interval(self, seconds:float) -> str:
        seconds=max(0,int(seconds or 0))
        if seconds<90: return f'{seconds}s'
        minutes=max(1,round(seconds/60))
        if minutes<90: return f'{minutes} min'
        hours=minutes/60
        return f'{hours:.1f} hr' if hours<10 and hours%1 else f'{round(hours)} hr'

    def _smart_retry_seconds(self, row:dict[str,Any], rec:dict[str,Any], cfg:dict[str,Any], now:float) -> int:
        base=max(15,int(cfg.get('automatic_retry_minutes') or 60))*60
        if not bool(cfg.get('automatic_smart_retry_enabled',True)):
            return base
        misses=max(1,int(rec.get('no_match_count') or 0)+1)
        date=str(row.get('date') or '')[:10]
        age_days=None
        if date:
            try:
                then=datetime.fromisoformat(date).date(); age_days=(datetime.now().date()-then).days
            except Exception: pass
        if age_days is not None and -1<=age_days<=2:
            return min(base,15*60)
        factor=1 if misses<=2 else 2 if misses<=4 else 4 if misses<=7 else 6
        return min(6*3600,max(base,base*factor))

    def _feed_cycle_interval(self, cfg:dict[str,Any]) -> int:
        full=max(5,int(cfg.get('automatic_search_interval_minutes') or 15))*60
        if bool(cfg.get('automatic_feed_enabled',True)):
            feed=max(2,int(cfg.get('automatic_feed_interval_minutes') or 5))*60
            return min(full,feed)
        return full

    def automation_health(self):
        cfg=self.public_config(); lib=self._library(); wanted=self.wanted(); rt=self._auto_runtime(); roots=[]
        seen=set()
        for kind,key in (('TV','tv_roots'),('Movies','movie_roots')):
            for raw in cfg.get(key) or []:
                path=str(raw or '').strip()
                if not path or path.casefold() in seen: continue
                seen.add(path.casefold()); roots.append({'kind':kind,'path':path,'online':Path(path).expanduser().exists()})
        idx=self.public_indexers(); enabled=[x for x in idx if x.get('enabled',True)]
        blacklists=[]
        for key,rec in (rt.get('targets') or {}).items():
            if not isinstance(rec,dict): continue
            for b in rec.get('blacklist') or []:
                if isinstance(b,dict): blacklists.append({'target_key':str(key),'target_label':str(rec.get('label') or key),**b})
        ih=[]
        for key,rec in (rt.get('indexer_health') or {}).items():
            if not isinstance(rec,dict): continue
            penalty=self._indexer_penalty(rt,str(rec.get('name') or key))
            ih.append({'name':str(rec.get('name') or key),'penalty':penalty,'recent_failures':sum(1 for x in rec.get('failures') or [] if time.time()-float(x)<24*3600),'recent_successes':sum(1 for x in rec.get('successes') or [] if time.time()-float(x)<24*3600)})
        metadata={'url':str(cfg.get('metadata_service_url') or ''),'status':'ready' if not str((rt.get('last_error') or '')).lower().startswith('metadata') else 'warning','last_refresh_ts':float(rt.get('last_metadata_refresh_ts') or 0)}
        needs_attention=[]
        try:
            snap=self.download_manager.snapshot()
            for pkg in snap.get('collections') or []:
                if str(pkg.get('post_status') or '')!='needs_attention': continue
                ctx=pkg.get('automation_context') if isinstance(pkg.get('automation_context'),dict) else {}
                if str(ctx.get('source') or '')!='automation_grab': continue
                needs_attention.append({'collection_id':str(pkg.get('id') or ''),'name':str(pkg.get('name') or 'Automation package'),'message':str(pkg.get('post_message') or 'Import needs attention'),'item_id':str(ctx.get('item_id') or ''),'target_key':str(ctx.get('target_key') or '')})
        except Exception: pass
        quiet=self._quiet_hours_state(cfg)
        return {'metadata':metadata,'roots':roots,'roots_online':sum(1 for x in roots if x['online']),'roots_total':len(roots),'indexers_enabled':len(enabled),'indexers_total':len(idx),'indexer_health':sorted(ih,key=lambda x:x['penalty'],reverse=True),'monitored_tv':sum(1 for x in lib if x.get('kind')=='tv' and x.get('monitored',True)),'monitored_movies':sum(1 for x in lib if x.get('kind')=='movie' and x.get('monitored',True)),'wanted_missing':len(wanted.get('missing') or []),'wanted_upgrades':len(wanted.get('upgrades') or []),'active_targets':len(self._auto_active_targets()),'blacklist_count':len(blacklists),'blacklists':sorted(blacklists,key=lambda x:float(x.get('failed_ts') or 0),reverse=True)[:100],'needs_attention':needs_attention,'needs_attention_count':len(needs_attention),'automatic_enabled':bool(cfg.get('automatic_grab_enabled')),'feed_enabled':bool(cfg.get('automatic_feed_enabled',True)),'last_feed_poll_ts':float(rt.get('last_feed_poll_ts') or 0),'last_feed_count':int(rt.get('last_feed_count') or 0),'last_feed_errors':list(rt.get('last_feed_errors') or [])[:5],'quiet_hours':quiet}

    def automatic_status(self):
        cfg=self.public_config(); rt=self._auto_runtime(); last=float(rt.get('last_cycle_ts') or 0)
        interval=self._feed_cycle_interval(cfg)
        next_ts=(last+interval) if cfg.get('automatic_grab_enabled') and last else (time.time() if cfg.get('automatic_grab_enabled') else 0)
        quiet=self._quiet_hours_state(cfg)
        feed_interval=max(2,int(cfg.get('automatic_feed_interval_minutes') or 5))*60
        last_feed=float(rt.get('last_feed_poll_ts') or 0)
        thread=self.auto_thread
        target_states={}
        rows=[]
        for key,rec in (rt.get('targets') or {}).items():
            if not isinstance(rec,dict): continue
            rows.append((float(rec.get('updated_ts') or rec.get('last_search_ts') or 0),str(key),rec))
        for _,key,rec in sorted(rows,reverse=True)[:120]:
            target_states[key]={'status':str(rec.get('status') or ''),'message':str(rec.get('message') or ''),'updated_ts':float(rec.get('updated_ts') or 0),'last_grab_title':str(rec.get('last_grab_title') or ''),'last_selection_reason':str(rec.get('last_selection_reason') or ''),'last_candidates':list(rec.get('last_candidates') or [])[:5]}
        for key,live in self._auto_download_states().items():
            target_states[key]={**target_states.get(key,{}),**live}
        return {
            'enabled':bool(cfg.get('automatic_grab_enabled')),
            'running':bool(thread and thread.is_alive()),
            'last_cycle_ts':last,
            'next_cycle_ts':next_ts,
            'last_result':str(rt.get('last_result') or ''),
            'last_error':str(rt.get('last_error') or ''),
            'last_grabs':list(rt.get('last_grabs') or [])[:10],
            'last_searches':int(rt.get('last_searches') or 0),
            'last_grab_count':int(rt.get('last_grab_count') or 0),
            'last_metadata_refresh_ts':float(rt.get('last_metadata_refresh_ts') or 0),
            'last_library_scan_ts':float(rt.get('last_library_scan_ts') or 0),
            'active_targets':len(self._auto_active_targets()),
            'target_states':target_states,
            'blacklist_count':sum(len((r or {}).get('blacklist') or []) for r in (rt.get('targets') or {}).values() if isinstance(r,dict)),
            'indexer_health':list(self.automation_health().get('indexer_health') or []),
            'feed_enabled':bool(cfg.get('automatic_feed_enabled',True)),
            'last_feed_poll_ts':last_feed,
            'next_feed_poll_ts':(last_feed+feed_interval) if last_feed else (time.time() if cfg.get('automatic_feed_enabled',True) else 0),
            'last_feed_count':int(rt.get('last_feed_count') or 0),
            'last_feed_matches':int(rt.get('last_feed_matches') or 0),
            'last_feed_errors':list(rt.get('last_feed_errors') or [])[:5],
            'quiet_hours':quiet,
            'smart_retry_enabled':bool(cfg.get('automatic_smart_retry_enabled',True)),
        }

    def refresh_monitored_metadata(self, *, force:bool=False, ident:str='') -> dict[str,Any]:
        """Refresh monitored metadata, preferring TMDB through NewzDeck Metadata Service.

        Existing TVmaze/Wikidata records are migrated only when an exact title/year
        match is found. File state and per-episode monitoring choices are preserved.
        """
        lib=self._library(); now=time.time(); cfg=self.public_config(); max_age=max(1,int(cfg.get('automatic_metadata_refresh_hours') or 6))*3600
        fetched={}; errors=[]; migrated=0
        for item in lib:
            if not isinstance(item,dict) or not item.get('monitored',True): continue
            if ident and str(item.get('id') or '')!=str(ident): continue
            if not force and now-self._iso_epoch(item.get('metadata_refreshed_at'))<max_age: continue
            ident=str(item.get('id') or ''); kind='tv' if item.get('kind')=='tv' else 'movie'
            tmdb_id=int(item.get('tmdb_id')) if str(item.get('tmdb_id') or '').isdigit() else 0
            match=None
            try:
                if not tmdb_id:
                    match=self._find_tmdb_match_for_legacy(item)
                    if match and match.get('tmdb_id'): tmdb_id=int(match['tmdb_id'])
                if tmdb_id:
                    if kind=='tv':
                        bundle=self._metadata_tv_bundle(tmdb_id)
                        series=bundle.get('series') if isinstance(bundle.get('series'),dict) else {}
                        canonical=str(series.get('title') or item.get('title') or '').strip()
                        ambiguous=bool(item.get('title_ambiguous'))
                        if canonical:
                            try:
                                rows=self._metadata_service_search('tv',canonical,None); target=_norm(canonical)
                                ambiguous=any(target in {_norm(r.get('title')),_norm(r.get('original_title'))} and str(r.get('tmdb_id') or r.get('metadata_id') or '')!=str(tmdb_id) for r in rows)
                            except Exception: pass
                        fetched[ident]={'kind':'tv','source':'tmdb','bundle':bundle,'migrate':str(item.get('metadata_provider') or '').lower()!='tmdb','title_ambiguous':ambiguous}
                    else: fetched[ident]={'kind':'movie','source':'tmdb','movie':self._metadata_movie_detail(tmdb_id),'migrate':str(item.get('metadata_provider') or '').lower()!='tmdb'}
                    continue
            except Exception as exc:


                if str(item.get('metadata_provider') or '').lower()=='tmdb':
                    errors.append({'item_id':ident,'title':str(item.get('title') or ''),'error':str(exc)}); continue
            try:
                if kind=='tv' and item.get('metadata_provider')=='tvmaze' and item.get('tvmaze_id'):
                    show_id=int(item.get('tvmaze_id')); show=self._tvmaze(f'shows/{show_id}',{},0); episodes=self._tvmaze(f'shows/{show_id}/episodes',{'specials':'1'},0)
                    fetched[ident]={'kind':'tv','source':'tvmaze','show':show,'episodes':list(episodes or [])}
                elif kind=='movie' and item.get('metadata_provider')=='wikidata' and item.get('wikidata_id'):
                    qid=str(item.get('wikidata_id') or '').upper(); raw=self._wikidata({'action':'wbgetentities','ids':qid,'props':'labels|descriptions|claims|sitelinks','languages':'en','languagefallback':'1'},0); ent=((raw.get('entities') or {}).get(qid) or {})
                    if ent and ent.get('missing') is None: fetched[ident]={'kind':'movie','source':'wikidata','movie':self._movie_from_entity(ent,False)}
            except Exception as exc:
                errors.append({'item_id':ident,'title':str(item.get('title') or ''),'error':str(exc)})
        updated=0; added_episodes=0; discovered=[]
        if fetched:
            with self.lock:
                fresh=self._library(); today=datetime.now().date().isoformat()
                for item in fresh:
                    ident=str(item.get('id') or ''); data=fetched.get(ident)
                    if not data: continue
                    before_keys={(int(s.get('season_number') or 0),int(e.get('episode_number') or 0)) for s in item.get('seasons') or [] for e in s.get('episodes') or []} if item.get('kind')=='tv' else set()
                    before_count=len(before_keys)
                    source=data.get('source')
                    if source=='tmdb':
                        if data.get('kind')=='tv':
                            self._apply_tmdb_tv(item,data.get('bundle') or {},migrate=bool(data.get('migrate')))
                            if 'title_ambiguous' in data: item['title_ambiguous']=bool(data.get('title_ambiguous'))
                            self._refresh_tv_library_identity(item,allow_network=False)
                        else: self._apply_tmdb_movie(item,data.get('movie') or {},migrate=bool(data.get('migrate')))
                        if data.get('migrate'): migrated+=1
                    elif data.get('kind')=='tv':
                        show=data.get('show') or {}; image=show.get('image') or {}; premiered=_date(show.get('premiered'))
                        item.update({'title':str(show.get('name') or item.get('title') or ''),'overview':self._strip_html(show.get('summary')) or item.get('overview',''),'first_air_date':premiered or item.get('first_air_date',''),'status':str(show.get('status') or item.get('status') or 'Unknown'),'poster_url':str(image.get('original') or image.get('medium') or item.get('poster_url') or ''),'genres':list(show.get('genres') or item.get('genres') or []),'rating':(show.get('rating') or {}).get('average') if isinstance(show.get('rating'),dict) else item.get('rating'),'network':str(((show.get('webChannel') or show.get('network') or {}).get('name')) or item.get('network') or ''),'language':str(show.get('language') or item.get('language') or '')})
                        if premiered[:4].isdigit(): item['year']=int(premiered[:4])
                        seasons={int(x.get('season_number') or 0):x for x in item.get('seasons') or [] if int(x.get('season_number') or 0)>0}; mode=str(item.get('monitor_mode') or 'all')
                        for epd in data.get('episodes') or []:
                            sn=int(epd.get('season') or 0); en=int(epd.get('number') or 0)
                            if sn<=0 or en<=0: continue
                            season=seasons.get(sn)
                            if season is None: season={'season_number':sn,'name':f'Season {sn}','air_date':'','monitored':mode!='none','episodes':[]}; seasons[sn]=season
                            eps={int(x.get('episode_number') or 0):x for x in season.get('episodes') or []}; air=_date(epd.get('airdate')); ep=eps.get(en)
                            if ep is None:
                                monitored=False if mode=='none' else bool(air and air>=today) if mode=='future' else bool(season.get('monitored',True))
                                ep={'episode_number':en,'name':str(epd.get('name') or f'Episode {en}'),'air_date':air,'overview':self._strip_html(epd.get('summary')),'monitored':monitored,'has_file':False,'file_path':'','file_quality':'','cutoff_met':False,'tvmaze_episode_id':epd.get('id')}; season.setdefault('episodes',[]).append(ep)
                            else: ep.update({'name':str(epd.get('name') or ep.get('name') or f'Episode {en}'),'air_date':air or ep.get('air_date',''),'overview':self._strip_html(epd.get('summary')) or ep.get('overview',''),'tvmaze_episode_id':epd.get('id') or ep.get('tvmaze_episode_id')})
                        for season in seasons.values():
                            season['episodes']=sorted(season.get('episodes') or [],key=lambda e:int(e.get('episode_number') or 0)); dates=[str(e.get('air_date') or '') for e in season['episodes'] if e.get('air_date')]
                            if dates: season['air_date']=min(dates)
                        item['seasons']=sorted(seasons.values(),key=lambda x:int(x.get('season_number') or 0))
                    else:
                        movie=data.get('movie') or {}; release=_date(movie.get('release_date'))
                        item.update({'title':str(movie.get('title') or item.get('title') or ''),'overview':str(movie.get('overview') or item.get('overview') or ''),'release_date':release or item.get('release_date',''),'runtime':movie.get('runtime') or item.get('runtime'),'imdb_id':str(movie.get('imdb_id') or item.get('imdb_id') or ''),'wikipedia_title':str(movie.get('wikipedia_title') or item.get('wikipedia_title') or '')})
                        if movie.get('year'): item['year']=movie.get('year')
                    after_count=sum(len(s.get('episodes') or []) for s in item.get('seasons') or []) if item.get('kind')=='tv' else 0
                    if item.get('kind')=='tv' and after_count>before_count:
                        for season in item.get('seasons') or []:
                            sn=int(season.get('season_number') or 0)
                            for ep in season.get('episodes') or []:
                                en=int(ep.get('episode_number') or 0)
                                if sn>0 and en>0 and (sn,en) not in before_keys:
                                    discovered.append({'item_id':ident,'title':str(item.get('title') or ''),'season':sn,'episode':en,'episode_name':str(ep.get('name') or f'Episode {en}'),'air_date':str(ep.get('air_date') or ''),'monitored':bool(ep.get('monitored',True))})
                    added_episodes+=max(0,after_count-before_count)
                    item['metadata_refreshed_at']=_now(); item['updated_at']=_now(); updated+=1
                self._save_library(fresh)
        for row in discovered[:80]:
            self._event('episode-discovered',f"Discovered {row['title']} S{row['season']:02d}E{row['episode']:02d} - {row['episode_name']}",**row)
        if updated or errors:
            self._event('metadata',f'Refreshed metadata for {updated} monitored title(s)',updated=updated,new_episodes=added_episodes,migrated_to_tmdb=migrated,errors=len(errors))
        return {'ok':True,'updated':updated,'new_episodes':added_episodes,'migrated_to_tmdb':migrated,'errors':errors}

    def _auto_release_matches(self, item:dict[str,Any], row:dict[str,Any], release:dict[str,Any], profile:dict[str,Any], *, upgrade:bool=False) -> bool:
        title=str(release.get('title') or '')
        if not title: return False
        if re.search(r'(?i)(?:^|[ ._\-])(sample|trailer|proof|extras?|password(?:ed)?|encrypted|repair[ ._\-]*only)(?:[ ._\-]|$)',title): return False
        if not _slug_match(title,str(item.get('title') or ''),item.get('year') if item.get('kind')=='movie' else None): return False
        parsed=release.get('parsed') if isinstance(release.get('parsed'),dict) else parse_release(title)
        if not bool(release.get('accepted')): return False
        if item.get('kind')=='tv':
            try: sn=int(row.get('season') or 0)
            except Exception: return False
            if bool(row.get('season_pack')):
                if sn<=0 or int(parsed.get('season') or 0)!=sn or not bool(parsed.get('is_season_pack')): return False
            else:
                try: en=int(row.get('episode') or 0)
                except Exception: return False
                if int(parsed.get('season') or 0)!=sn or int(parsed.get('episode') or 0)!=en: return False
                if bool(parsed.get('is_multi_episode')) or bool(parsed.get('is_season_pack')): return False
        if upgrade:
            current=str(row.get('current_quality') or 'Unknown')
            if self._quality_rank(str(parsed.get('quality') or ''),profile)>=self._quality_rank(current,profile): return False
        return True

    def _auto_backlog_eligible(self, row:dict[str,Any], item:dict[str,Any], cfg:dict[str,Any]) -> bool:
        if bool(cfg.get('automatic_backlog_enabled')): return True
        enabled=self._iso_epoch(cfg.get('automatic_enabled_at'))
        if enabled<=0: return False
        enabled_date=datetime.fromtimestamp(enabled,timezone.utc).date().isoformat()
        date=str(row.get('date') or '')
        if item.get('kind')=='movie':

            if self._iso_epoch(item.get('added_at'))>=enabled: return True
            return bool(date and date>=enabled_date)
        return bool(date and date>=enabled_date)

    def _season_pack_rows(self, missing_rows:list[dict[str,Any]], lib:dict[str,dict[str,Any]]) -> list[dict[str,Any]]:
        """Build conservative season-pack targets from fully aired seasons.

        NewzDeck only auto-prefers a pack after every known monitored episode in the
        season has aired. This avoids grabbing rolling/incomplete season bundles.
        """
        today=datetime.now().date().isoformat(); grouped={}
        for row in missing_rows:
            if str(row.get('kind') or '')!='tv': continue
            try: key=(str(row.get('item_id') or ''),int(row.get('season') or 0))
            except Exception: continue
            if not key[0] or key[1]<=0: continue
            grouped.setdefault(key,[]).append(row)
        out=[]
        for (item_id,sn),rows in grouped.items():
            if len(rows)<2: continue
            item=lib.get(item_id)
            season=next((x for x in (item or {}).get('seasons') or [] if int(x.get('season_number') or 0)==sn),None)
            eps=[x for x in (season or {}).get('episodes') or [] if bool(x.get('monitored',True)) and int(x.get('episode_number') or 0)>0]
            if len(eps)<2: continue
            if any(not str(ep.get('air_date') or '') or str(ep.get('air_date') or '')>today for ep in eps): continue
            missing_nums=sorted({int(x.get('episode') or 0) for x in rows if int(x.get('episode') or 0)>0})
            if len(missing_nums)<2: continue
            out.append({
                'item_id':item_id,'kind':'tv','title':str((item or {}).get('title') or rows[0].get('title') or ''),
                'season':sn,'episode':None,'season_pack':True,'pack_episode_numbers':missing_nums,
                'pack_known_episode_numbers':sorted(int(x.get('episode_number') or 0) for x in eps),
                'date':max((str(x.get('date') or '') for x in rows),default=''),
                'label':f"{(item or {}).get('title') or rows[0].get('title')} Season {sn} pack",
                'reason_code':'season_pack','reason_label':'Season pack opportunity',
                'reason_detail':f'{len(missing_nums)} released episodes are missing in a fully aired season.',
                'auto_type':'season_pack',
            })
        return out

    def _automatic_cycle(self, *, force:bool=False):
        cfg=self.public_config()
        if not bool(cfg.get('automatic_grab_enabled')):
            return {'ok':False,'disabled':True,'message':'Automatic downloads are disabled'}
        rt=self._auto_runtime(); now=time.time(); last_grabs=[]; searches=0; grabs=0; skipped=0; feed_matches=0; errors=[]
        try:
            blacklisted_now=self._sync_automatic_failures(rt)
            if blacklisted_now: self._save_auto_runtime(rt)
            metadata_due=force or now-float(rt.get('last_metadata_refresh_ts') or 0)>=max(1,int(cfg.get('automatic_metadata_refresh_hours') or 6))*3600
            if metadata_due:
                meta=self.refresh_monitored_metadata(force=True); rt['last_metadata_refresh_ts']=time.time(); rt['last_metadata_result']=meta
            scan_due=force or now-float(rt.get('last_library_scan_ts') or 0)>=max(5,int(cfg.get('automatic_library_scan_minutes') or 30))*60
            if scan_due:
                try: rt['last_library_scan_result']=self.scan_library(); rt['last_library_scan_ts']=time.time()
                except Exception as exc: errors.append(f'Library scan: {exc}')

            feed_due=force or now-float(rt.get('last_feed_poll_ts') or 0)>=max(2,int(cfg.get('automatic_feed_interval_minutes') or 5))*60
            feed_rows=self._poll_release_feed(rt,cfg,force=feed_due)

            wanted=self.wanted(); missing_rows=[dict(x,auto_type='missing') for x in wanted.get('missing') or []]
            lib={str(x.get('id') or ''):x for x in self._library() if isinstance(x,dict)}
            rows=[]
            if bool(cfg.get('automatic_season_packs_enabled',True)):
                rows.extend(self._season_pack_rows(missing_rows,lib))
            rows.extend(missing_rows)
            if bool(cfg.get('automatic_upgrades_enabled')):
                rows += [dict(x,auto_type='upgrade') for x in wanted.get('upgrades') or []]
            rows.sort(key=lambda x:(1 if x.get('season_pack') else 0,str(x.get('date') or ''),str(x.get('label') or '')),reverse=True)
            active=self._auto_active_targets(); targets=rt.get('targets') if isinstance(rt.get('targets'),dict) else {}; rt['targets']=targets
            queue_depth=max(1,int(cfg.get('automatic_queue_depth') or 25)); max_grabs=max(0,queue_depth-len(active)); max_searches=max(12,min(250,max(1,max_grabs)*5))
            release_delay=max(0,int(cfg.get('automatic_release_delay_minutes') or 0))*60
            quiet=self._quiet_hours_state(cfg)
            if quiet.get('active') and not force:
                rt.update({'last_cycle_ts':time.time(),'last_searches':0,'last_grab_count':0,'last_grabs':[],'last_error':' | '.join(errors[:5]),'last_result':f"Quiet hours active until {datetime.fromtimestamp(float(quiet.get('resume_ts') or 0)).strftime('%H:%M') if quiet.get('resume_ts') else quiet.get('end')} • monitored feed {len(feed_rows)} recent release(s)",'last_active_target_count':len(active),'last_feed_matches':0,'targets':targets,'quiet_active':True})
                self._save_auto_runtime(rt)
                return {'ok':True,'quiet':True,'searched':0,'grabbed':0,'skipped':len(rows),'feed_count':len(feed_rows),'errors':errors}
            rt['quiet_active']=False

            for row in rows:
                if grabs>=max_grabs or searches>=max_searches: break
                item=lib.get(str(row.get('item_id') or ''))
                if not item or not self._auto_backlog_eligible(row,item,cfg): skipped+=1; continue
                root=self._resolve_root(item)
                if not root or not root.exists():
                    key=self._auto_target_key(row=row); rec=targets.setdefault(key,{}) if key else {}; rec.update({'status':'needs_root','updated_ts':now,'message':'Configured Root Folder is unavailable'})
                    skipped+=1; continue
                key=self._auto_target_key(row=row)
                if not key: continue
                try: pack_key=f"tv:{row.get('item_id')}:s{int(row.get('season') or 0):02d}:pack"
                except Exception: pack_key=''
                if not row.get('season_pack') and pack_key and pack_key in active: skipped+=1; continue
                if key in active:
                    targets.setdefault(key,{}).update({'status':'queued','updated_ts':now,'message':'Download already queued'}); skipped+=1; continue
                rec=targets.setdefault(key,{})
                rec.update({'item_id':str(row.get('item_id') or ''),'label':str(row.get('label') or ''),'kind':str(row.get('kind') or ''),'season':row.get('season'),'episode':row.get('episode'),'season_pack':bool(row.get('season_pack')),'updated_ts':now})
                profile=next((p for p in self._profiles() if str(p.get('id'))==str(item.get('quality_profile_id'))),self._profiles()[0])

                candidates=self._feed_candidates_for_target(item,row,profile,feed_rows,rt,rec,now,release_delay) if feed_rows else []
                from_feed=bool(candidates)
                if from_feed:
                    feed_matches+=1; rec.update({'status':'release_detected','message':f"New release detected on {candidates[0].get('indexer') or 'indexer'}",'updated_ts':now})
                    self._event('release-detected',f"Detected {candidates[0].get('title')}",item_id=str(row.get('item_id') or ''),target_key=key,target=row.get('label'),indexer=str(candidates[0].get('indexer') or ''),quality=str((candidates[0].get('parsed') or {}).get('quality') or ''))
                else:
                    next_search=float(rec.get('next_search_ts') or 0)
                    full_interval=max(5,int(cfg.get('automatic_search_interval_minutes') or 15))*60
                    if next_search<=0 and float(rec.get('last_search_ts') or 0)>0:
                        next_search=float(rec.get('last_search_ts') or 0)+full_interval
                    if not force and now<next_search: skipped+=1; continue
                    searches+=1; rec.update({'last_search_ts':now,'updated_ts':now,'status':'searching','message':'Scheduled Wanted search'})
                    try:
                        result=self.search_releases(str(row.get('item_id') or ''),row.get('season'),row.get('episode'))
                        profile=result.get('profile') if isinstance(result.get('profile'),dict) else profile
                        rec['last_candidates']=[{'title':str(x.get('title') or ''),'score':int(x.get('effective_score') or x.get('score') or 0),'decision':str(x.get('decision') or ''),'quality':str((x.get('parsed') or {}).get('quality') or ''),'indexer':str(x.get('indexer') or '')} for x in (result.get('releases') or [])[:8]]
                        attempted=[x for x in rec.get('attempted_releases') or [] if isinstance(x,dict) and now-float(x.get('ts') or 0)<12*3600]
                        attempted_guids={str(x.get('guid') or '').casefold() for x in attempted if x.get('guid')}
                        blacklist=[x for x in rec.get('blacklist') or [] if isinstance(x,dict)]
                        blacklist_guids={str(x.get('guid') or '').casefold() for x in blacklist if x.get('guid')}; blacklist_titles={str(x.get('title') or '').casefold() for x in blacklist if x.get('title')}
                        candidates=[]
                        for rel in result.get('releases') or []:
                            guid=str(rel.get('guid') or rel.get('download_url') or '').casefold()
                            if guid and (guid in attempted_guids or guid in blacklist_guids): continue
                            if str(rel.get('title') or '').casefold() in blacklist_titles: continue
                            published=float(rel.get('published') or 0)
                            if release_delay and published>0 and now-published<release_delay: continue
                            if self._auto_release_matches(item,row,rel,profile,upgrade=row.get('auto_type')=='upgrade'):
                                penalty=self._indexer_penalty(rt,str(rel.get('indexer') or ''),now); rel=dict(rel); rel['automation_indexer_penalty']=penalty; rel['automation_effective_score']=int(rel.get('score') or 0)-penalty; candidates.append(rel)
                        candidates.sort(key=lambda x:(int(x.get('automation_effective_score') or -99999),int(x.get('published') or 0)),reverse=True)
                    except Exception as exc:
                        msg=str(exc); errors.append(f"{row.get('label')}: {msg}"); rec.update({'status':'error','message':msg,'next_search_ts':now+min(max(15,int(cfg.get('automatic_retry_minutes') or 60))*60,30*60)}); continue

                attempted=[x for x in rec.get('attempted_releases') or [] if isinstance(x,dict) and now-float(x.get('ts') or 0)<12*3600]
                if not candidates:
                    rec['no_match_count']=int(rec.get('no_match_count') or 0)+1
                    delay=self._smart_retry_seconds(row,rec,cfg,now)
                    rec.update({'status':'waiting','message':f'No acceptable release found • retry in {self._human_interval(delay)}','next_search_ts':now+delay,'attempted_releases':attempted})
                    continue
                rel=dict(candidates[0]); rel.update({'automatic':True,'target_key':key,'auto_type':row.get('auto_type') or 'missing','season_pack':bool(row.get('season_pack')),'pack_episode_numbers':list(row.get('pack_episode_numbers') or []),'pack_known_episode_numbers':list(row.get('pack_known_episode_numbers') or [])})
                grabbed=self.grab_release(rel)
                active.add(key)
                if bool(grabbed.get('already_queued')):
                    skipped+=1
                    rec.update({'status':'queued','message':str(grabbed.get('reason') or 'Download already queued by another NewzDeck runtime'),'updated_ts':time.time(),'last_collection_id':str(grabbed.get('collection_id') or rec.get('last_collection_id') or '')})
                    continue
                grabs+=1
                guid=str(rel.get('guid') or rel.get('download_url') or ''); attempted.append({'guid':guid,'title':str(rel.get('title') or ''),'ts':now})
                rec.update({'status':'grabbed','message':f"Queued {rel.get('title')}",'last_grab_ts':now,'last_grab_guid':guid,'last_grab_title':str(rel.get('title') or ''),'last_collection_id':str(grabbed.get('collection_id') or ''),'next_search_ts':0,'attempted_releases':attempted[-8:],'last_indexer':str(rel.get('indexer') or ''),'last_effective_score':int(rel.get('automation_effective_score') or rel.get('score') or 0),'last_selection_reason':' • '.join(list(rel.get('reasons') or [])[:4]),'no_match_count':0,'selection_source':'feed' if from_feed else 'scheduled-search'})
                last_grabs.append({'target':str(row.get('label') or ''),'release':str(rel.get('title') or ''),'collection_id':str(grabbed.get('collection_id') or ''),'source':'feed' if from_feed else 'search'})
                self._event('auto-grab',f"Automatically grabbed {rel.get('title')}",item_id=str(row.get('item_id') or ''),target_key=key,target=row.get('label'),collection=grabbed.get('collection_name'),collection_id=grabbed.get('collection_id'),score=rel.get('score'),effective_score=rel.get('automation_effective_score'),indexer_penalty=rel.get('automation_indexer_penalty'),quality=str((rel.get('parsed') or {}).get('quality') or ''),season_pack=bool(row.get('season_pack')),selection_source='feed' if from_feed else 'scheduled-search')

            active_after=len(self._auto_active_targets())
            rt.update({'last_cycle_ts':time.time(),'last_searches':searches,'last_grab_count':grabs,'last_grabs':last_grabs,'last_error':' | '.join(errors[:5]),'last_result':f'Feed {len(feed_rows)} recent • {feed_matches} matched • searched {searches} target(s) • queued {grabs} • Automation queue {active_after}/{queue_depth} • skipped {skipped}','last_active_target_count':active_after,'last_feed_matches':feed_matches,'targets':targets})
            self._save_auto_runtime(rt)
            if searches or grabs or errors or feed_matches: self._event('auto-cycle',rt['last_result'],errors=len(errors),feed_matches=feed_matches)
            return {'ok':True,'searched':searches,'grabbed':grabs,'skipped':skipped,'feed_count':len(feed_rows),'feed_matches':feed_matches,'grabs':last_grabs,'errors':errors}
        except Exception as exc:
            rt.update({'last_cycle_ts':time.time(),'last_error':str(exc),'last_result':f'Automation cycle failed: {exc}'})
            self._save_auto_runtime(rt); self._event('auto-error',f'Automatic download cycle failed: {exc}')
            raise

    @contextlib.contextmanager
    def _automatic_process_guard(self):
        """Allow only one desktop/service process to run an Auto Grab cycle."""
        self.automation_cycle_lock_file.parent.mkdir(parents=True,exist_ok=True)
        fh=self.automation_cycle_lock_file.open('a+b')
        acquired=False
        try:
            fh.seek(0,os.SEEK_END)
            if fh.tell()<=0:
                fh.write(b'0'); fh.flush()
            fh.seek(0)
            try:
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(fh.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                acquired=True
            except OSError:
                acquired=False
            yield acquired
        finally:
            if acquired:
                try:
                    fh.seek(0)
                    if os.name=='nt':
                        import msvcrt
                        msvcrt.locking(fh.fileno(),msvcrt.LK_UNLCK,1)
                    else:
                        import fcntl
                        fcntl.flock(fh.fileno(),fcntl.LOCK_UN)
                except OSError:
                    pass
            fh.close()

    def _automatic_worker(self, force:bool=False):
        if not self.auto_run_lock.acquire(blocking=False): return
        try:
            with self._automatic_process_guard() as owner:
                if owner:
                    self._automatic_cycle(force=force)
        finally:
            self.auto_run_lock.release()

    def _reconcile_worker(self):
        if not self.reconcile_lock.acquire(blocking=False): return
        try:
            result=self.scan_library(); rt=self._auto_runtime(); rt['last_library_scan_ts']=time.time(); rt['last_library_scan_result']={'matched':result.get('matched',0),'files_scanned':result.get('files_scanned',0),'changes':len(result.get('changes') or []),'offline_roots':len(result.get('offline_roots') or [])}; self._save_auto_runtime(rt)
        finally: self.reconcile_lock.release()

    def maybe_reconcile_library(self):
        if self.reconcile_thread and self.reconcile_thread.is_alive(): return {'started':False,'running':True}
        if not self._library(): return {'started':False,'empty':True}
        cfg=self.public_config(); rt=self._auto_runtime(); interval=max(5,int(cfg.get('automatic_library_scan_minutes') or 30))*60
        if float(rt.get('last_library_scan_ts') or 0)>0 and time.time()-float(rt.get('last_library_scan_ts') or 0)<interval: return {'started':False,'due':False}
        self.reconcile_thread=threading.Thread(target=self._reconcile_worker,name='newzdeck-library-reconcile',daemon=True); self.reconcile_thread.start(); return {'started':True}

    def maybe_run_automatic(self):
        cfg=self.public_config()
        if not bool(cfg.get('automatic_grab_enabled')): return {'started':False,'disabled':True}
        if self.auto_thread and self.auto_thread.is_alive(): return {'started':False,'running':True}
        rt=self._auto_runtime(); interval=self._feed_cycle_interval(cfg)
        active_now=len(self._auto_active_targets()); prior_active=int(rt.get('last_active_target_count') or 0); queue_depth=max(1,int(cfg.get('automatic_queue_depth') or 25))
        refill_due=bool(active_now<queue_depth and prior_active>active_now)
        if float(rt.get('last_cycle_ts') or 0)>0 and time.time()-float(rt.get('last_cycle_ts') or 0)<interval and not refill_due: return {'started':False,'due':False}
        self.auto_thread=threading.Thread(target=self._automatic_worker,name='newzdeck-media-auto-grab',daemon=True)
        self.auto_thread.start(); return {'started':True}

    def run_automatic_now(self):
        cfg=self.public_config()
        if not bool(cfg.get('automatic_grab_enabled')): raise ValueError('Enable Automatic Downloads in Automation Setup first')
        if self.auto_thread and self.auto_thread.is_alive(): return {'ok':True,'started':False,'running':True}
        self.auto_thread=threading.Thread(target=lambda:self._automatic_worker(True),name='newzdeck-media-auto-grab-manual',daemon=True)
        self.auto_thread.start(); return {'ok':True,'started':True}

    def _metadata_cache(self):
        x = _read(self.metadata_cache_file, {})
        return x if isinstance(x, dict) else {}

    def _cache_get(self, key: str, max_age: int = 86400):
        with self.metadata_cache_lock:
            cache = self._metadata_cache()
            rec = cache.get(str(key))
            if not isinstance(rec, dict): return None
            try:
                if time.time() - float(rec.get('ts') or 0) > max_age: return None
            except Exception:
                return None
            return rec.get('value')

    def _cache_put(self, key: str, value):
        try:
            with self.metadata_cache_lock:
                cache = self._metadata_cache()
                cache[str(key)] = {'ts': time.time(), 'value': value}
                if len(cache) > 500:
                    rows = sorted(cache.items(), key=lambda kv: float((kv[1] or {}).get('ts') or 0), reverse=True)[:400]
                    cache = dict(rows)
                _write(self.metadata_cache_file, cache)
        except Exception:
            pass
        return value

    def _metadata_cloud_state(self) -> dict[str,Any]:
        value=_read(self.metadata_cloud_state_file,{})
        if isinstance(value,dict) and value:
            return value
        rt=self._auto_runtime(); legacy=rt.get('metadata_cloud') if isinstance(rt.get('metadata_cloud'),dict) else {}
        return dict(legacy)

    def _metadata_note_state(self, *, ok: bool, error: str = '', cached: bool = False, health: dict[str,Any] | None = None):
        try:
            with self.metadata_state_lock:
                cloud=self._metadata_cloud_state(); now=time.time()
                if ok:
                    cloud['last_success_ts']=now
                    if health and isinstance(health,dict):
                        cloud['server_version']=str(health.get('version') or cloud.get('server_version') or '')
                        cloud['auth_mode']=str(health.get('auth_mode') or cloud.get('auth_mode') or '')
                        cloud['api_version']=int(health.get('api_version') or cloud.get('api_version') or 0)
                        cloud['min_client_version']=str(health.get('min_client_version') or cloud.get('min_client_version') or '')
                        cloud['tmdb_status']=str(health.get('tmdb_status') or cloud.get('tmdb_status') or 'unknown')
                        cloud['tmdb_last_success_ts']=float(health.get('tmdb_last_success_ts') or cloud.get('tmdb_last_success_ts') or 0)
                        cloud['tmdb_last_error_ts']=float(health.get('tmdb_last_error_ts') or cloud.get('tmdb_last_error_ts') or 0)
                        cloud['tmdb_last_error']=str(health.get('tmdb_last_error') or cloud.get('tmdb_last_error') or '')[:500]
                        cloud['tmdb_stale_fallbacks']=int(health.get('tmdb_stale_fallbacks') or cloud.get('tmdb_stale_fallbacks') or 0)
                    if not cached:
                        cloud['last_error']=''; cloud['last_error_ts']=0
                if error:
                    cloud['last_error']=str(error)[:500]; cloud['last_error_ts']=now
                if cached:
                    cloud['cached_fallbacks']=int(cloud.get('cached_fallbacks') or 0)+1
                    cloud['last_cached_fallback_ts']=now
                cloud['updated_ts']=now; _write(self.metadata_cloud_state_file,cloud)
        except Exception:
            pass

    def metadata_service_status_snapshot(self) -> dict[str,Any]:
        c=self._config(); cloud=self._metadata_cloud_state(); now=time.time()
        success=float(cloud.get('last_success_ts') or 0); error_ts=float(cloud.get('last_error_ts') or 0)
        circuit_open,circuit_remaining,circuit_reason=self._metadata_circuit_state()
        upstream_status=str(cloud.get('tmdb_status') or 'unknown').lower()
        if circuit_open or upstream_status in {'degraded','offline'}:
            status='degraded'
        elif error_ts > success:
            status='degraded' if success and now-success < 86400 else 'offline'
        elif success and now-success < 900:
            status='online'
        elif success:
            status='idle'
        else:
            status='unknown'
        minimum=str(cloud.get('min_client_version') or '')
        compatible=not minimum or _version_tuple(self.version) >= _version_tuple(minimum)
        installation_id=str(c.get('metadata_installation_id') or '')
        return {
            'status':status,'url':self._metadata_service_base(),'authenticated':bool(str(c.get('metadata_access_token_protected') or '').strip()),
            'installation_id':installation_id,'server_version':str(cloud.get('server_version') or ''),'api_version':int(cloud.get('api_version') or 0),
            'min_client_version':minimum,'compatible':compatible,'last_success_ts':success,'last_error_ts':error_ts,'last_error':str(cloud.get('last_error') or ''),
            'cached_fallbacks':int(cloud.get('cached_fallbacks') or 0),'last_cached_fallback_ts':float(cloud.get('last_cached_fallback_ts') or 0),
            'tmdb_status':upstream_status,'tmdb_last_success_ts':float(cloud.get('tmdb_last_success_ts') or 0),
            'tmdb_last_error_ts':float(cloud.get('tmdb_last_error_ts') or 0),'tmdb_last_error':str(cloud.get('tmdb_last_error') or ''),
            'tmdb_stale_fallbacks':int(cloud.get('tmdb_stale_fallbacks') or 0),
            'circuit_open':circuit_open,'circuit_retry_seconds':int(circuit_remaining+0.999) if circuit_open else 0,'circuit_reason':circuit_reason,
        }

    def public_config(self):
        c=self._config()
        return {
            'tv_roots':list(c.get('tv_roots') or []),
            'movie_roots':list(c.get('movie_roots') or []),
            'metadata_provider':'newzdeck-metadata',
            'metadata_service_url':str(c.get('metadata_service_url') or 'https://api.newzdeck.com').rstrip('/'),
            'metadata_service_cloud':str(c.get('metadata_service_url') or '').rstrip('/').lower()=='https://api.newzdeck.com',
            'metadata_service_authenticated':bool(str(c.get('metadata_access_token_protected') or '').strip()),
            'metadata_tv':{'provider':'TMDB via NewzDeck Metadata Service','configured':True,'key_required':False,'detail':'Primary TV, season, episode and artwork metadata; TVmaze fallback remains available'},
            'metadata_movies':{'provider':'TMDB via NewzDeck Metadata Service','configured':True,'key_required':False,'detail':'Primary movie and artwork metadata; Wikidata fallback remains available'},
            'tmdb_configured':False,
            'tmdb_optional':False,
            'automatic_grab_enabled':bool(c.get('automatic_grab_enabled', False)),
            'automatic_backlog_enabled':bool(c.get('automatic_backlog_enabled', False)),
            'automatic_upgrades_enabled':bool(c.get('automatic_upgrades_enabled', False)),
            'automatic_season_packs_enabled':bool(c.get('automatic_season_packs_enabled', True)),
            'automatic_feed_enabled':bool(c.get('automatic_feed_enabled', True)),
            'automatic_feed_interval_minutes':max(2,min(60,int(c.get('automatic_feed_interval_minutes',5) or 5))),
            'automatic_smart_retry_enabled':bool(c.get('automatic_smart_retry_enabled', True)),
            'automatic_quiet_hours_enabled':bool(c.get('automatic_quiet_hours_enabled', False)),
            'automatic_quiet_start':str(c.get('automatic_quiet_start') or '01:00')[:5],
            'automatic_quiet_end':str(c.get('automatic_quiet_end') or '07:00')[:5],
            'automatic_notifications_enabled':bool(c.get('automatic_notifications_enabled', False)),
            'automatic_search_interval_minutes':max(5,min(180,int(c.get('automatic_search_interval_minutes',15) or 15))),
            'automatic_retry_minutes':max(15,min(720,int(c.get('automatic_retry_minutes',60) or 60))),
            'automatic_release_delay_minutes':max(0,min(180,int(c.get('automatic_release_delay_minutes',5) or 0))),
            'automatic_queue_depth':max(1,min(100,int(c.get('automatic_queue_depth',25) or 25))),
            'automatic_metadata_refresh_hours':max(1,min(48,int(c.get('automatic_metadata_refresh_hours',6) or 6))),
            'automatic_library_scan_minutes':max(5,min(360,int(c.get('automatic_library_scan_minutes',30) or 30))),
            'automatic_storage_reserve_gb':max(1,min(100,int(c.get('automatic_storage_reserve_gb',5) or 5))),
            'automatic_movie_availability':str(c.get('automatic_movie_availability') or 'digital_physical') if str(c.get('automatic_movie_availability') or 'digital_physical') in {'digital_physical','theatrical'} else 'digital_physical',
            'automatic_enabled_at':str(c.get('automatic_enabled_at') or ''),
            'plex_organize_enabled':bool(c.get('plex_organize_enabled', True)),
            'plex_replace_upgrades':bool(c.get('plex_replace_upgrades', True)),
            'plex_cleanup_staging':bool(c.get('plex_cleanup_staging', True)),
            'plex_include_quality':bool(c.get('plex_include_quality', False)),
            'tv_folder_template':str(c.get('tv_folder_template') or '{library_title}'),
            'tv_season_template':str(c.get('tv_season_template') or 'Season {season}'),
            'tv_file_template':str(c.get('tv_file_template') or '{library_title} - {episode_token} - {episode_title}'),
            'movie_folder_template':str(c.get('movie_folder_template') or '{title} ({year})'),
            'movie_file_template':str(c.get('movie_file_template') or '{title} ({year})'),
        }

    def save_config(self, data:dict[str,Any]):
        with self.lock:
            c=self._config(); changed_root_keys=set()
            for k in ('tv_roots','movie_roots'):
                if k in data and isinstance(data[k],list):
                    vals=[]; seen=set()
                    for x in data[k]:
                        p=str(x or '').strip(); key=p.casefold()
                        if p and key not in seen:
                            vals.append(p); seen.add(key)
                    c[k]=vals[:20]; changed_root_keys.add(k)
            if 'metadata_service_url' in data:
                raw_url=str(data.get('metadata_service_url') or '').strip().rstrip('/')
                if not raw_url:
                    raw_url='https://api.newzdeck.com'
                parsed=urllib.parse.urlparse(raw_url)
                if parsed.scheme not in ('http','https') or not parsed.netloc:
                    raise ValueError('Metadata Service URL must be a valid http:// or https:// address')
                c['metadata_service_url']=raw_url[:500]

            key=str(data.get('tmdb_api_key') or '').strip()
            if key: c['tmdb_api_key_protected']=self.protect_secret(key)
            if data.get('clear_tmdb_key'): c.pop('tmdb_api_key_protected',None)
            prior_auto=bool(c.get('automatic_grab_enabled',False))
            for k in ('plex_organize_enabled','plex_replace_upgrades','plex_cleanup_staging','plex_include_quality','automatic_grab_enabled','automatic_backlog_enabled','automatic_upgrades_enabled','automatic_season_packs_enabled','automatic_feed_enabled','automatic_smart_retry_enabled','automatic_quiet_hours_enabled','automatic_notifications_enabled'):
                if k in data: c[k]=bool(data.get(k))
            if bool(c.get('automatic_grab_enabled',False)) and not prior_auto:
                c['automatic_enabled_at']=_now()
            for k,lo,hi,default in (
                ('automatic_search_interval_minutes',5,180,15),('automatic_feed_interval_minutes',2,60,5),('automatic_retry_minutes',15,720,60),
                ('automatic_release_delay_minutes',0,180,5),('automatic_queue_depth',1,100,25),
                ('automatic_metadata_refresh_hours',1,48,6),('automatic_library_scan_minutes',5,360,30),
                ('automatic_storage_reserve_gb',1,100,5)):
                if k in data:
                    try: c[k]=max(lo,min(hi,int(data.get(k) if data.get(k) is not None else default)))
                    except Exception: c[k]=default
            for k,default in (('automatic_quiet_start','01:00'),('automatic_quiet_end','07:00')):
                if k in data:
                    text=str(data.get(k) or default).strip()
                    if not re.match(r'^(?:[01]\d|2[0-3]):[0-5]\d$',text): raise ValueError(f'{k.replace("automatic_","" ).replace("_"," ").title()} must use HH:MM')
                    c[k]=text
            if 'automatic_movie_availability' in data:
                mode=str(data.get('automatic_movie_availability') or 'digital_physical')
                if mode not in {'digital_physical','theatrical'}: raise ValueError('Unknown movie availability policy')
                c['automatic_movie_availability']=mode
            for k in ('tv_folder_template','tv_season_template','tv_file_template','movie_folder_template','movie_file_template'):
                if k in data:
                    value=str(data.get(k) or '').strip()
                    if value: c[k]=value[:240]
            _write(self.config_file,c)


            if changed_root_keys:
                lib=self._library(); adjusted=False
                for item in lib:
                    key='tv_roots' if item.get('kind')=='tv' else 'movie_roots'
                    if key not in changed_root_keys: continue
                    assigned=str(item.get('root_folder') or '').strip()
                    allowed={str(v or '').strip().casefold() for v in c.get(key) or [] if str(v or '').strip()}
                    if assigned and assigned.casefold() not in allowed:
                        item['root_folder']=''; item['updated_at']=_now(); adjusted=True
                if adjusted: self._save_library(lib)
            return self.public_config()

    def migrate_secrets_machine_scope(self):
        changed=0
        with self.lock:
            c=self._config(); v=str(c.get('tmdb_api_key_protected') or '')
            if v and not v.startswith('dpapim:'):
                try:
                    plain=self.unprotect_secret(v); c['tmdb_api_key_protected']=self.protect_secret(plain, True); changed+=1
                except Exception: pass
            for secret_key in ('metadata_installation_secret_protected','metadata_access_token_protected'):
                v=str(c.get(secret_key) or '')
                if v and not v.startswith('dpapim:'):
                    try:
                        plain=self.unprotect_secret(v); c[secret_key]=self.protect_secret(plain, True); changed+=1
                    except Exception: pass
            _write(self.config_file,c)
            idx=self._indexers()
            for rec in idx:
                v=str(rec.get('api_key_protected') or '')
                if v and not v.startswith('dpapim:'):
                    try:
                        plain=self.unprotect_secret(v); rec['api_key_protected']=self.protect_secret(plain, True); changed+=1
                    except Exception: pass
            _write(self.indexers_file,idx)
        return changed

    def _tmdb_key(self):
        v=str(self._config().get('tmdb_api_key_protected') or '')
        return self.unprotect_secret(v) if v else ''

    def _http_json(self,url:str,timeout=20,headers:dict[str,str]|None=None,method:str='GET',payload:dict[str,Any]|None=None):
        """HTTP JSON with a true wall-clock deadline.

        urllib's socket timeout is an inactivity timeout and can still be exceeded
        by DNS/platform networking edge cases.  Run the request in a daemon worker
        and bound the entire operation so a metadata call can never pin a local
        NewzDeck HTTP handler forever.
        """
        h={'User-Agent':f'NewzDeck/{self.version} (+desktop media manager)','Accept':'application/json'}
        h.update(headers or {})
        body=None
        if payload is not None:
            body=json.dumps(payload,separators=(',',':')).encode('utf-8')
            h['Content-Type']='application/json'
        req=urllib.request.Request(url,data=body,headers=h,method=str(method or 'GET').upper())
        result: queue.Queue = queue.Queue(maxsize=1)
        def worker():
            try:
                with urllib.request.urlopen(req,timeout=max(0.5,float(timeout))) as r:
                    raw=r.read(8*1024*1024)
                result.put((True,json.loads(raw.decode('utf-8','replace'))))
            except BaseException as exc:
                try: result.put((False,exc),block=False)
                except Exception: pass
        threading.Thread(target=worker,name='newzdeck-metadata-http',daemon=True).start()
        try:
            ok,value=result.get(timeout=max(0.25,float(timeout))+0.50)
        except queue.Empty as exc:
            raise TimeoutError(f'HTTP request exceeded {timeout} seconds') from exc
        if ok: return value
        raise value

    def _http_bytes_deadline(self,url:str,timeout:float=10.0,headers:dict[str,str]|None=None,max_bytes:int=12*1024*1024) -> bytes:
        """Read an HTTP response with a true wall-clock deadline.

        ``urllib`` only applies its timeout to individual blocking socket operations.
        DNS resolution, proxy discovery and some TLS/platform networking paths can
        therefore keep a Newznab search handler alive far longer than requested.
        Run the blocking request in a daemon thread and bound the caller by wall
        clock so one unhealthy indexer can never pin Interactive Search.
        """
        req=urllib.request.Request(url,headers=dict(headers or {}))
        result: queue.Queue = queue.Queue(maxsize=1)
        limit=max(1024,int(max_bytes or 0))
        deadline=max(0.5,float(timeout))
        def worker():
            try:
                with urllib.request.urlopen(req,timeout=deadline) as r:
                    raw=r.read(limit+1)
                if len(raw)>limit:
                    raise ValueError(f'Indexer response exceeded {limit//(1024*1024)} MB')
                result.put((True,raw),block=False)
            except BaseException as exc:
                try: result.put((False,exc),block=False)
                except Exception: pass
        threading.Thread(target=worker,name='newzdeck-indexer-http',daemon=True).start()
        try:
            ok,value=result.get(timeout=deadline+0.50)
        except queue.Empty as exc:
            raise TimeoutError(f'Indexer request exceeded {deadline:g} seconds') from exc
        if ok: return value
        raise value

    def _metadata_circuit_state(self) -> tuple[bool,float,str]:
        with self.metadata_circuit_lock:
            remaining=max(0.0,float(self.metadata_circuit_open_until or 0)-time.time())
            return remaining>0,remaining,str(self.metadata_circuit_reason or '')

    def _metadata_circuit_trip(self, reason:str, seconds:float=45.0):
        with self.metadata_circuit_lock:
            self.metadata_circuit_open_until=max(float(self.metadata_circuit_open_until or 0),time.time()+max(5.0,float(seconds)))
            self.metadata_circuit_reason=str(reason or 'Metadata Service temporarily unavailable')[:500]

    def _metadata_circuit_reset(self):
        with self.metadata_circuit_lock:
            self.metadata_circuit_open_until=0.0
            self.metadata_circuit_reason=''

    def _metadata_service_base(self) -> str:
        env=str(os.environ.get('NEWZDECK_METADATA_URL') or '').strip().rstrip('/')
        if env: return env
        return str(self._config().get('metadata_service_url') or 'https://api.newzdeck.com').strip().rstrip('/')

    def _metadata_installation_credentials(self) -> tuple[str,str,str]:
        c=self._config()
        installation_id=str(c.get('metadata_installation_id') or '').strip()
        secret_protected=str(c.get('metadata_installation_secret_protected') or '')
        token_protected=str(c.get('metadata_access_token_protected') or '')
        bootstrap=''; token=''
        try: bootstrap=self.unprotect_secret(secret_protected) if secret_protected else ''
        except Exception: bootstrap=''
        try: token=self.unprotect_secret(token_protected) if token_protected else ''
        except Exception: token=''

        if not installation_id or not bootstrap:
            installation_id='install_'+secrets.token_hex(16)
            bootstrap=secrets.token_urlsafe(40)
            c['metadata_installation_id']=installation_id
            c['metadata_installation_secret_protected']=self.protect_secret(bootstrap)
            c.pop('metadata_access_token_protected',None)
            token=''
            _write(self.config_file,c)
        return installation_id,bootstrap,token

    def _metadata_clear_access_token(self):
        with self.lock:
            c=self._config()
            if 'metadata_access_token_protected' in c:
                c.pop('metadata_access_token_protected',None); _write(self.config_file,c)

    def _metadata_register_installation(self) -> str:
        base=self._metadata_service_base()
        installation_id,bootstrap,_=self._metadata_installation_credentials()
        url=base+'/v1/installations/register'
        value=self._http_json(url,12,{'X-NewzDeck-Client':self.version},'POST',{
            'installation_id':installation_id,
            'bootstrap_secret':bootstrap,
            'client_version':self.version,
            'platform':'windows' if os.name=='nt' else os.name,
        })
        token=str((value or {}).get('token') or '').strip()
        if not token:
            raise ValueError('Metadata Service did not issue an installation credential')
        with self.lock:
            c=self._config(); c['metadata_access_token_protected']=self.protect_secret(token); c['metadata_authenticated_at']=_now(); _write(self.config_file,c)
        return token

    def _metadata_api(self, path:str, params:dict[str,Any]|None=None, timeout:int=12):
        base=self._metadata_service_base()
        if not base: raise ValueError('NewzDeck Metadata Service URL is not configured')
        query=urllib.parse.urlencode({k:v for k,v in (params or {}).items() if v is not None and str(v)!=''})
        path_text='/'+str(path or '').lstrip('/')
        url=base+path_text+('?' + query if query else '')
        public_path=path_text=='/health' or path_text=='/v1/installations/register'
        installation_id,_,token=self._metadata_installation_credentials()
        cacheable=path_text not in {'/health','/v1/installations/me','/v1/installations/register'}
        cache_key='cloud:'+url

        circuit_open,circuit_remaining,circuit_reason=self._metadata_circuit_state()
        if circuit_open and not public_path:
            if cacheable:
                cached=self._cache_get(cache_key,30*86400)
                if cached is not None:
                    self._metadata_note_state(ok=False,error=circuit_reason or 'Metadata Service circuit breaker is open',cached=True)
                    return cached
            raise ValueError(f'Metadata Service is temporarily paused after a network failure; retry in {max(1,int(circuit_remaining+0.999))} seconds')

        def request_with(current_token:str):
            headers={'X-NewzDeck-Client':self.version,'X-NewzDeck-Installation':installation_id}
            if current_token: headers['Authorization']='Bearer '+current_token
            return self._http_json(url,timeout,headers)

        def success(value):
            if cacheable and isinstance(value,(dict,list)):
                self._cache_put(cache_key,value)
            self._metadata_circuit_reset()
            self._metadata_note_state(ok=True,health=value if path_text=='/health' and isinstance(value,dict) else None)
            return value

        def cached_or_raise(message:str, exc:Exception):
            if cacheable:
                cached=self._cache_get(cache_key,30*86400)
                if cached is not None:
                    self._metadata_note_state(ok=False,error=message,cached=True)
                    return cached
            self._metadata_note_state(ok=False,error=message)
            raise ValueError(message) from exc

        try:

            return success(request_with('' if public_path else token))
        except urllib.error.HTTPError as exc:
            if exc.code==401 and not public_path:
                try:
                    self._metadata_clear_access_token()
                    fresh=self._metadata_register_installation()
                    return success(request_with(fresh))
                except urllib.error.HTTPError as reg_exc:
                    detail=''
                    try:
                        detail=reg_exc.read(4096).decode('utf-8','replace'); parsed=json.loads(detail); detail=str(parsed.get('detail') or detail)
                    except Exception: pass
                    message=f'Metadata Service authentication failed (HTTP {reg_exc.code})' + (f': {detail[:240]}' if detail else '')
                    self._metadata_note_state(ok=False,error=message); raise ValueError(message) from reg_exc
            detail=''
            retry_after=str(exc.headers.get('Retry-After') or '').strip() if getattr(exc,'headers',None) else ''
            try:
                detail=exc.read(4096).decode('utf-8','replace')
                parsed=json.loads(detail); detail=str(parsed.get('detail') or parsed.get('error') or detail)
            except Exception: pass
            if exc.code==429:
                wait=f' Retry in about {retry_after} seconds.' if retry_after.isdigit() else ''
                return cached_or_raise('NewzDeck Metadata Service rate limit reached.'+wait,exc)
            if 500 <= int(exc.code) <= 599:
                self._metadata_circuit_trip(f'Metadata Service returned HTTP {exc.code}',20)
                return cached_or_raise(f'Metadata Service temporarily returned HTTP {exc.code}',exc)
            message=f'Metadata Service returned HTTP {exc.code}' + (f': {detail[:240]}' if detail else '')
            self._metadata_note_state(ok=False,error=message); raise ValueError(message) from exc
        except (urllib.error.URLError,TimeoutError,OSError) as exc:
            reason=f'Cannot reach NewzDeck Metadata Service at {base}: {exc}'
            self._metadata_circuit_trip(reason,45)
            return cached_or_raise(reason,exc)

    def test_metadata_service(self):
        started=time.perf_counter(); value=self._metadata_api('/health',timeout=4)
        if not isinstance(value,dict) or not value.get('ok'):
            raise ValueError('Metadata Service did not return a healthy response')
        auth_mode=str(value.get('auth_mode') or 'open')
        minimum=str(value.get('min_client_version') or '')
        compatible=not minimum or _version_tuple(self.version) >= _version_tuple(minimum)
        if not compatible:
            raise ValueError(f'NewzDeck v{self.version} is too old for Metadata Service v{value.get("version") or "?"}. Update NewzDeck to at least v{minimum}.')
        authenticated=False; installation_id=''
        if auth_mode.lower()=='installation':
            me=self._metadata_api('/v1/installations/me',timeout=8)
            authenticated=bool((me or {}).get('ok'))
            installation_id=str((me or {}).get('installation_id') or '')
        self._metadata_note_state(ok=True,health=value)
        return {'ok':True,'url':self._metadata_service_base(),'latency_ms':round((time.perf_counter()-started)*1000,1),'service':value.get('service'),'version':value.get('version'),'tmdb_configured':bool(value.get('tmdb_configured')),'tmdb_status':str(value.get('tmdb_status') or 'unknown'),'tmdb_last_error':str(value.get('tmdb_last_error') or ''),'auth_mode':auth_mode,'authenticated':authenticated,'installation_id':installation_id,'api_version':int(value.get('api_version') or 0),'min_client_version':minimum,'compatible':compatible}

    def _proxy_summary(self, row:dict[str,Any], kind:str|None=None) -> dict[str,Any]:
        media_kind='tv' if str(kind or row.get('media_type') or '').lower()=='tv' else 'movie'
        images=row.get('images') if isinstance(row.get('images'),dict) else {}
        tid=row.get('tmdb_id')
        return {
            'provider':'tmdb','metadata_provider':'tmdb','metadata_id':str(tid or ''),'tmdb_id':int(tid) if str(tid or '').isdigit() else None,
            'kind':media_kind,'title':str(row.get('title') or 'Untitled'),'original_title':str(row.get('original_title') or ''),
            'year':int(row.get('year')) if str(row.get('year') or '').isdigit() else None,'date':_date(row.get('release_date')),
            'release_date':_date(row.get('release_date')),'overview':str(row.get('overview') or ''),'poster_url':str(images.get('poster') or images.get('poster_original') or ''),
            'backdrop_url':str(images.get('backdrop') or images.get('backdrop_original') or ''),'genres':list(row.get('genres') or []),'rating':row.get('rating'),
            'popularity':float(row.get('popularity') or 0),'vote_count':int(row.get('vote_count') or 0),'language':str(row.get('original_language') or '')
        }

    def _metadata_service_search(self, kind:str, query:str, year:int|None=None) -> list[dict[str,Any]]:
        data=self._metadata_api('/v1/search',{'q':query,'type':kind,'year':year},8)
        return [self._proxy_summary(x,kind) for x in list((data or {}).get('results') or []) if isinstance(x,dict)][:40]

    def _metadata_tv_bundle(self, tmdb_id:int) -> dict[str,Any]:
        try:
            bundle=self._metadata_api(f'/v1/tv/{int(tmdb_id)}/automation',timeout=25)
            if isinstance(bundle,dict) and isinstance(bundle.get('series'),dict): return bundle
        except Exception:

            pass
        series=self._metadata_api(f'/v1/tv/{int(tmdb_id)}',timeout=15)
        seasons=[]
        for sr in list((series or {}).get('seasons') or []):
            try: sn=int(sr.get('season_number') or 0)
            except Exception: sn=0
            if sn<=0: continue
            try: seasons.append(self._metadata_api(f'/v1/tv/{int(tmdb_id)}/season/{sn}',timeout=15))
            except Exception: continue
        return {'series':series,'seasons':seasons}

    def _metadata_movie_detail(self, tmdb_id:int) -> dict[str,Any]:
        value=self._metadata_api(f'/v1/movie/{int(tmdb_id)}',timeout=15)
        return value if isinstance(value,dict) else {}

    def _find_tmdb_match_for_legacy(self, item:dict[str,Any]) -> dict[str,Any]|None:
        title=str(item.get('title') or '').strip(); kind='tv' if item.get('kind')=='tv' else 'movie'
        if not title: return None
        try: rows=self._metadata_service_search(kind,title,int(item.get('year')) if str(item.get('year') or '').isdigit() else None)
        except Exception: return None
        target=_norm(title); year=int(item.get('year')) if str(item.get('year') or '').isdigit() else None
        exact=[]
        for row in rows:
            names={_norm(row.get('title')),_norm(row.get('original_title'))}
            if target not in names: continue
            row_year=row.get('year')
            if year and row_year and int(row_year)!=year: continue
            exact.append(row)
        if not exact: return None
        exact.sort(key=lambda x:(int(bool(year and x.get('year')==year)),float(x.get('popularity') or 0),int(x.get('vote_count') or 0)),reverse=True)
        return exact[0]

    def _apply_tmdb_movie(self, item:dict[str,Any], detail:dict[str,Any], *, migrate:bool=False):
        summary=self._proxy_summary(detail,'movie'); images=detail.get('images') if isinstance(detail.get('images'),dict) else {}
        external=detail.get('external_ids') if isinstance(detail.get('external_ids'),dict) else {}
        if migrate and str(item.get('metadata_provider') or '').lower()!='tmdb':
            item['legacy_metadata']={'provider':item.get('metadata_provider'),'metadata_id':item.get('metadata_id'),'tvmaze_id':item.get('tvmaze_id'),'wikidata_id':item.get('wikidata_id')}
        item.update({
            'metadata_provider':'tmdb','provider':'tmdb','metadata_id':str(summary.get('tmdb_id') or ''),'tmdb_id':summary.get('tmdb_id'),
            'title':summary.get('title') or item.get('title'),'original_title':summary.get('original_title') or item.get('original_title',''),
            'overview':summary.get('overview') or item.get('overview',''),'release_date':summary.get('release_date') or item.get('release_date',''),
            'theatrical_release_date':_date(detail.get('theatrical_release_date')) or item.get('theatrical_release_date',''),
            'digital_release_date':_date(detail.get('digital_release_date')) or item.get('digital_release_date',''),
            'physical_release_date':_date(detail.get('physical_release_date')) or item.get('physical_release_date',''),
            'availability_date':_date(detail.get('availability_date')) or item.get('availability_date',''),
            'certification':str(detail.get('certification') or item.get('certification') or ''),
            'year':summary.get('year') or item.get('year'),'status':str(detail.get('status') or item.get('status') or 'Unknown'),
            'poster_url':summary.get('poster_url') or item.get('poster_url',''),'backdrop_url':summary.get('backdrop_url') or item.get('backdrop_url',''),
            'genres':summary.get('genres') or item.get('genres') or [],'rating':summary.get('rating') if summary.get('rating') is not None else item.get('rating'),
            'runtime':detail.get('runtime_minutes') or item.get('runtime'),'language':summary.get('language') or item.get('language',''),
            'external_ids':external,'imdb_id':str(external.get('imdb') or item.get('imdb_id') or ''),'metadata_source':'NewzDeck Metadata Service / TMDB'
        })
        return item

    def _apply_tmdb_tv(self, item:dict[str,Any], bundle:dict[str,Any], *, migrate:bool=False):
        detail=bundle.get('series') if isinstance(bundle.get('series'),dict) else {}; summary=self._proxy_summary(detail,'tv')
        external=detail.get('external_ids') if isinstance(detail.get('external_ids'),dict) else {}; networks=list(detail.get('networks') or [])
        if migrate and str(item.get('metadata_provider') or '').lower()!='tmdb':
            item['legacy_metadata']={'provider':item.get('metadata_provider'),'metadata_id':item.get('metadata_id'),'tvmaze_id':item.get('tvmaze_id'),'wikidata_id':item.get('wikidata_id')}
        item.update({
            'metadata_provider':'tmdb','provider':'tmdb','metadata_id':str(summary.get('tmdb_id') or ''),'tmdb_id':summary.get('tmdb_id'),
            'title':summary.get('title') or item.get('title'),'original_title':summary.get('original_title') or item.get('original_title',''),
            'overview':summary.get('overview') or item.get('overview',''),'first_air_date':summary.get('release_date') or item.get('first_air_date',''),
            'year':summary.get('year') or item.get('year'),'status':str(detail.get('status') or item.get('status') or 'Unknown'),
            'poster_url':summary.get('poster_url') or item.get('poster_url',''),'backdrop_url':summary.get('backdrop_url') or item.get('backdrop_url',''),
            'genres':summary.get('genres') or item.get('genres') or [],'rating':summary.get('rating') if summary.get('rating') is not None else item.get('rating'),
            'network':str(networks[0] if networks else item.get('network') or ''),'language':summary.get('language') or item.get('language',''),
            'country_codes':[str(x).upper() for x in list(detail.get('countries') or item.get('country_codes') or []) if str(x).strip()],
            'external_ids':external,'imdb_id':str(external.get('imdb') or item.get('imdb_id') or ''),'tvdb_id':external.get('tvdb') or item.get('tvdb_id'),
            'metadata_source':'NewzDeck Metadata Service / TMDB'
        })
        old_seasons={int(x.get('season_number') or 0):x for x in item.get('seasons') or [] if int(x.get('season_number') or 0)>0}
        mode=str(item.get('monitor_mode') or 'all'); today=datetime.now().date().isoformat(); new_seasons=[]
        for sd in list(bundle.get('seasons') or []):
            try: sn=int(sd.get('season_number') or 0)
            except Exception: sn=0
            if sn<=0: continue
            old_s=old_seasons.get(sn) or {}; old_eps={int(x.get('episode_number') or 0):x for x in old_s.get('episodes') or []}
            season_monitored=bool(old_s.get('monitored',mode!='none'))
            eps=[]
            for epd in list(sd.get('episodes') or []):
                try: en=int(epd.get('episode_number') or 0)
                except Exception: en=0
                if en<=0: continue
                old=old_eps.get(en)
                air=_date(epd.get('air_date'))
                if old is not None:
                    ep=dict(old); monitored=bool(ep.get('monitored',season_monitored))
                else:
                    monitored=False if mode=='none' else bool(air and air>=today) if mode=='future' else season_monitored
                    ep={'has_file':False,'file_path':'','file_quality':'','cutoff_met':False,'monitored':monitored}
                ep.update({'episode_number':en,'name':str(epd.get('name') or ep.get('name') or f'Episode {en}'),'air_date':air or ep.get('air_date',''),'overview':str(epd.get('overview') or ep.get('overview') or ''),'tmdb_episode_id':epd.get('tmdb_id') or ep.get('tmdb_episode_id'),'still_url':str(epd.get('still') or ep.get('still_url') or ''),'rating':epd.get('rating') if epd.get('rating') is not None else ep.get('rating'),'monitored':monitored})
                eps.append(ep)
            new_seasons.append({'season_number':sn,'name':str(sd.get('name') or old_s.get('name') or f'Season {sn}'),'air_date':_date(sd.get('air_date')) or old_s.get('air_date',''),'poster_url':str(sd.get('poster') or old_s.get('poster_url') or ''),'monitored':season_monitored,'episodes':sorted(eps,key=lambda e:int(e.get('episode_number') or 0))})
        if new_seasons: item['seasons']=sorted(new_seasons,key=lambda x:int(x.get('season_number') or 0))
        return item

    def _tv_default_library_title(self, item:dict[str,Any], *, release_title:str='') -> str:
        title=str(item.get('title') or 'TV Show').strip() or 'TV Show'
        year=item.get('year') or ''
        release_tag=_release_tv_country_tag(release_title,title)
        codes=[_tv_country_tag(x) for x in list(item.get('country_codes') or [])]
        country=next((x for x in codes if x),'')
        ambiguous=bool(item.get('title_ambiguous'))
        if release_tag and (ambiguous or not country or release_tag==country):
            return f'{title} ({release_tag})'
        if ambiguous and country:
            return f'{title} ({country})'
        # The year is metadata, not part of the default TV library identity.
        # Automatic naming should therefore be ``Silo``, not ``Silo (2023)``.
        # Country/version suffixes are retained above only when they are needed
        # to disambiguate distinct same-title series (for example Big Brother (US)).
        return title

    def _refresh_tv_library_identity(self, item:dict[str,Any], *, allow_network:bool=True) -> str:
        """Persist a stable Plex/library name independently of TMDB's display title.

        A manual override always wins. Automatic names are the canonical series
        title only. A country suffix is used only when needed to disambiguate
        distinct same-title series; the metadata year is never appended by default.
        """
        if item.get('kind')!='tv': return str(item.get('title') or '')
        if str(item.get('library_title_source') or '').lower()=='manual' and str(item.get('library_title') or '').strip():
            return str(item.get('library_title')).strip()
        title=str(item.get('title') or '').strip()
        selected=str(item.get('tmdb_id') or item.get('metadata_id') or '')
        ambiguous=bool(item.get('title_ambiguous'))
        if allow_network and title and str(item.get('metadata_provider') or '').lower()=='tmdb':
            try:
                rows=self._metadata_service_search('tv',title,None)
                target=_norm(title); exact=[]
                for row in rows:
                    names={_norm(row.get('title')),_norm(row.get('original_title'))}
                    rid=str(row.get('tmdb_id') or row.get('metadata_id') or '')
                    if target in names and rid and rid!=selected: exact.append(row)
                ambiguous=bool(exact)
            except Exception:
                pass
        item['title_ambiguous']=ambiguous
        name=self._tv_default_library_title(item)
        item['library_title']=name; item['library_title_source']='auto'
        return name

    def _tv_library_title(self, item:dict[str,Any], *, release_title:str='') -> str:
        manual=str(item.get('library_title') or '').strip()
        if manual and str(item.get('library_title_source') or '').lower()=='manual': return manual
        release_tag=_release_tv_country_tag(release_title,item.get('title'))
        if release_tag:
            title=str(item.get('title') or 'TV Show').strip() or 'TV Show'
            return f'{title} ({release_tag})'
        # Recompute automatic identity instead of trusting a persisted pre-3.5.15
        # ``Title (Year)`` value. This makes the naming fix effective immediately
        # for existing Automation libraries without requiring the user to re-add a show.
        return self._tv_default_library_title(item,release_title=release_title)

    def _strip_html(self, value: Any) -> str:
        text = re.sub(r'<[^>]+>', ' ', str(value or ''))
        return re.sub(r'\s+', ' ', html.unescape(text)).strip()

    def _tvmaze(self, path:str, params:dict[str,Any]|None=None, cache_age:int=21600):
        q=urllib.parse.urlencode(params or {})
        url='https://api.tvmaze.com/'+path.lstrip('/')+('?' + q if q else '')
        key='tvmaze:'+url
        cached=self._cache_get(key, cache_age)
        if cached is not None: return cached
        try:
            value=self._http_json(url,12)
        except urllib.error.HTTPError as exc:
            if exc.code != 429: raise
            delay=2.0
            try: delay=max(delay,float(exc.headers.get('Retry-After') or 0))
            except Exception: pass
            time.sleep(min(delay,10.0))
            value=self._http_json(url,12)
        return self._cache_put(key,value)

    def _wikidata(self, params:dict[str,Any], cache_age:int=86400):
        q=dict(params); q.setdefault('format','json'); q.setdefault('origin','*'); q.setdefault('maxlag','5')
        url='https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode(q)
        key='wikidata:'+url
        cached=self._cache_get(key,cache_age)
        if cached is not None: return cached
        try:
            value=self._http_json(url,15)
        except urllib.error.HTTPError as exc:
            if exc.code != 429: raise
            delay=2.0
            try: delay=max(delay,float(exc.headers.get('Retry-After') or 0))
            except Exception: pass
            time.sleep(min(delay,10.0))
            value=self._http_json(url,15)
        return self._cache_put(key,value)

    def _wikipedia_summary(self, title:str, cache_age:int=604800):
        title=str(title or '').strip()
        if not title: return {}
        params={'action':'query','format':'json','redirects':'1','prop':'pageimages|extracts','exintro':'1','explaintext':'1','pithumbsize':'500','titles':title,'origin':'*'}
        url='https://en.wikipedia.org/w/api.php?'+urllib.parse.urlencode(params)
        key='wikipedia:'+url
        cached=self._cache_get(key,cache_age)
        if cached is not None: return cached
        data=self._http_json(url,15)
        pages=((data.get('query') or {}).get('pages') or {})
        page=next(iter(pages.values()),{}) if isinstance(pages,dict) else {}
        out={'extract':str(page.get('extract') or ''),'poster_url':str((page.get('thumbnail') or {}).get('source') or '')}
        return self._cache_put(key,out)

    def _claim_value(self, entity:dict[str,Any], prop:str):
        rows=((entity.get('claims') or {}).get(prop) or [])
        for row in rows:
            try:
                snak=row.get('mainsnak') or {}; dv=snak.get('datavalue') or {}; value=dv.get('value')
                if value is not None: return value
            except Exception: pass
        return None

    def _claim_date(self, entity:dict[str,Any], prop='P577') -> str:
        value=self._claim_value(entity,prop)
        if isinstance(value,dict): value=value.get('time')
        m=re.search(r'([12]\d{3})-(\d{2})-(\d{2})',str(value or ''))
        return '-'.join(m.groups()) if m else ''

    def _claim_quantity(self, entity:dict[str,Any], prop:str):
        value=self._claim_value(entity,prop)
        if isinstance(value,dict):
            try: return float(str(value.get('amount') or '0').lstrip('+'))
            except Exception: return None
        return None

    def _commons_thumbnail(self, filename:str, width:int=500) -> str:
        filename=str(filename or '').strip()
        if not filename: return ''
        params={'action':'query','format':'json','prop':'imageinfo','iiprop':'url','iiurlwidth':str(width),'titles':'File:'+filename,'origin':'*'}
        url='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)
        key='commons:'+url
        cached=self._cache_get(key,604800)
        if cached is not None: return str(cached or '')
        try:
            d=self._http_json(url); pages=((d.get('query') or {}).get('pages') or {})
            page=next(iter(pages.values()),{}) if isinstance(pages,dict) else {}
            ii=(page.get('imageinfo') or [{}])[0]
            out=str(ii.get('thumburl') or ii.get('url') or '')
        except Exception:
            out=''
        return str(self._cache_put(key,out) or '')

    def _wikidata_movie_entity(self, qid:str):
        qid=str(qid or '').strip().upper()
        if not re.fullmatch(r'Q\d+',qid): raise ValueError('Invalid Wikidata movie identifier')
        data=self._wikidata({'action':'wbgetentities','ids':qid,'props':'labels|descriptions|claims|sitelinks','languages':'en','languagefallback':'1'},604800)
        entity=((data.get('entities') or {}).get(qid) or {})
        if not entity or entity.get('missing') is not None: raise ValueError('Movie metadata could not be found')
        return entity

    def _movie_from_entity(self, entity:dict[str,Any], include_summary:bool=False):
        qid=str(entity.get('id') or '')
        title=str((((entity.get('labels') or {}).get('en') or {}).get('value')) or qid)
        desc=str((((entity.get('descriptions') or {}).get('en') or {}).get('value')) or '')
        release_date=self._claim_date(entity,'P577')
        year=int(release_date[:4]) if release_date[:4].isdigit() else None
        imdb=str(self._claim_value(entity,'P345') or '')
        runtime=self._claim_quantity(entity,'P2047')
        enwiki=str((((entity.get('sitelinks') or {}).get('enwiki') or {}).get('title')) or '')

        return {'provider':'wikidata','metadata_id':qid,'wikidata_id':qid,'kind':'movie','title':title,'year':year,'date':release_date,'release_date':release_date,'overview':desc,'poster_url':'','imdb_id':imdb,'runtime':runtime,'wikipedia_title':enwiki}

    def _tmdb(self,path:str,params:dict[str,Any]|None=None):

        key=self._tmdb_key()
        if not key: raise ValueError('Optional TMDB credentials are not configured')
        q=dict(params or {});q.setdefault('language','en-US')
        headers={'User-Agent':f'NewzDeck/{self.version}','Accept':'application/json'}
        if len(key)>40 or key.count('.')>=2 or key.startswith('eyJ'): headers['Authorization']='Bearer '+key
        else: q['api_key']=key
        url='https://api.themoviedb.org/3/'+path.lstrip('/')+'?'+urllib.parse.urlencode(q)
        return self._http_json(url,20,headers)

    def _legacy_metadata_search(self,kind:str,query:str):
        kind='tv' if str(kind).lower()=='tv' else 'movie'; q=str(query or '').strip()
        if not q: return []
        if kind=='tv':
            data=self._tvmaze('search/shows',{'q':q},3600)
            out=[]
            for row in list(data or [])[:24]:
                r=row.get('show') or {}; date=_date(r.get('premiered')); image=r.get('image') or {}
                out.append({'provider':'tvmaze','metadata_id':r.get('id'),'tvmaze_id':r.get('id'),'kind':'tv','title':str(r.get('name') or 'Untitled'),'year':int(date[:4]) if date[:4].isdigit() else None,'date':date,'overview':self._strip_html(r.get('summary')),'poster_url':str(image.get('medium') or image.get('original') or ''),'status':str(r.get('status') or 'Unknown'),'external_ids':r.get('externals') or {},'genres':list(r.get('genres') or []),'rating':(r.get('rating') or {}).get('average'),'popularity':int(r.get('weight') or 0)})
            return out
        search=self._wikidata({'action':'wbsearchentities','search':q,'language':'en','uselang':'en','type':'item','limit':'24'},3600)
        raw=list(search.get('search') or [])

        candidates=[x for x in raw if re.search(r'\b(?:film|movie|motion picture|documentary)\b',str(x.get('description') or ''),re.I)][:16]
        if not candidates: return []
        ids='|'.join(str(x.get('id') or '') for x in candidates if re.fullmatch(r'Q\d+',str(x.get('id') or '')))
        if not ids: return []
        data=self._wikidata({'action':'wbgetentities','ids':ids,'props':'labels|descriptions|claims|sitelinks','languages':'en','languagefallback':'1'},86400)
        entities=data.get('entities') or {}
        out=[]
        for rec in candidates:
            ent=entities.get(str(rec.get('id') or '')) or {}
            if not ent: continue
            try: item=self._movie_from_entity(ent,False)
            except Exception: continue
            if not item.get('overview'): item['overview']=str(rec.get('description') or '')
            out.append(item)
        return out

    def metadata_search(self,kind:str,query:str):
        kind='tv' if str(kind).lower()=='tv' else 'movie'; q=str(query or '').strip()
        if not q: return []
        try:
            rows=self._metadata_service_search(kind,q)
            if rows: return rows
        except Exception as exc:
            self._event('metadata-fallback',f'Metadata Service unavailable during {kind} search; using fallback',error=str(exc))
        return self._legacy_metadata_search(kind,q)



    def _discover_state(self):
        value=_read(self.discover_state_file,{})
        if not isinstance(value,dict): value={}
        for key in ('liked','hidden','viewed'):
            if not isinstance(value.get(key),dict): value[key]={}
        return value

    def _save_discover_state(self,value):
        _write(self.discover_state_file,value)

    def _discover_key(self,item:dict[str,Any])->str:
        provider=str(item.get('provider') or item.get('metadata_provider') or '').strip().lower()
        ident=str(item.get('metadata_id') or item.get('tmdb_id') or '').strip()
        if provider and ident: return f'{provider}:{ident}'
        return f"{str(item.get('kind') or '')}:{_norm(item.get('title'))}:{item.get('year') or ''}"

    def _discover_library_status(self,item:dict[str,Any]):
        provider=str(item.get('provider') or '').lower(); ident=str(item.get('metadata_id') or '')
        title=_norm(item.get('title')); year=item.get('year'); found=None
        for lib in self._library():
            lp=str(lib.get('metadata_provider') or '').lower(); li=str(lib.get('metadata_id') or '')
            if ident and lp==provider and li==ident: found=lib; break
            if provider=='tmdb' and str(item.get('tmdb_id') or '') and str(lib.get('tmdb_id') or '')==str(item.get('tmdb_id') or ''): found=lib; break
            if title and _norm(lib.get('title'))==title and (not year or not lib.get('year') or int(lib.get('year'))==int(year)):
                found=lib; break
        if not found: return {'in_library':False,'library_id':'','monitored':False,'wanted':False,'has_file':False}
        wanted=False;has_file=False
        if found.get('kind')=='movie':
            has_file=bool(found.get('movie_file')); wanted=bool(found.get('monitored',True) and not has_file and self._movie_available(found))
        else:
            aired=[ep for se in found.get('seasons') or [] for ep in se.get('episodes') or [] if ep.get('monitored',True) and self._aired(str(ep.get('air_date') or ''))]
            has_file=any(ep.get('has_file') for ep in aired); wanted=any(not ep.get('has_file') for ep in aired)
        return {'in_library':True,'library_id':str(found.get('id') or ''),'monitored':bool(found.get('monitored',True)),'wanted':wanted,'has_file':has_file}

    def _discover_decorate(self,items:list[dict[str,Any]]):
        state=self._discover_state(); hidden=state.get('hidden') or {}; liked=state.get('liked') or {}; out=[]
        for raw in items:
            item=dict(raw); key=self._discover_key(item)
            if key in hidden: continue
            item['discover_key']=key; item['liked']=key in liked; item['library_status']=self._discover_library_status(item); out.append(item)
        return out

    def _discover_proxy_section(self,row:dict[str,Any]):
        items=[self._proxy_summary(x,str(row.get('media_type') or '')) for x in list(row.get('results') or []) if isinstance(x,dict)]
        return {'id':str(row.get('key') or ''),'title':str(row.get('title') or 'Discover'),'subtitle':self._discover_section_subtitle(str(row.get('key') or '')),'items':self._discover_decorate(items)}

    def _discover_section_subtitle(self,key:str)->str:
        return {
            'trending_movies':'What movie fans are watching and talking about this week',
            'trending_tv':'TV series trending this week',
            'new_movies':'Recent digital and physical movie releases',
            'new_tv':'Recently premiered and newly arriving TV series',
            'airing_tv':'Series with episodes airing during the next seven days',
            'upcoming_movies':'Movies with upcoming theatrical releases',
            'top_rated_movies':'Highly rated movies with established audience votes',
            'top_rated_tv':'Highly rated television series',
            'coming_home':'Upcoming digital and physical releases',
            'in_theaters':'Movies currently playing in theaters',
            'coming_movies':'Upcoming theatrical releases',
            'airing_today':'TV episodes airing today',
            'airing':'TV episodes airing this week',
            'for_you':'Personalized from your library and Discover feedback',
        }.get(key,'Curated by TMDB and NewzDeck')

    def _discover_recommend(self,candidates:list[dict[str,Any]],limit:int=20):
        ds=self._discover_state(); taste={}
        def add_genres(genres,weight):
            for genre in genres or []:
                k=str(genre or '').strip().casefold()
                if k: taste[k]=taste.get(k,0)+weight
        for lib in self._library(): add_genres(lib.get('genres') or [],3)
        for rec in (ds.get('liked') or {}).values():
            if isinstance(rec,dict): add_genres(rec.get('genres') or [],7)
        scored=[];seen=set()
        for item in candidates:
            key=self._discover_key(item)
            if key in seen: continue
            seen.add(key); score=float(item.get('_recommend_weight') or 0)*12 + float(item.get('rating') or 0)*2 + min(18,float(item.get('popularity') or 0)/30)
            score+=sum(taste.get(str(g).casefold(),0) for g in item.get('genres') or [])
            if (item.get('library_status') or {}).get('in_library'): score-=10
            scored.append((score,item))
        scored.sort(key=lambda x:x[0],reverse=True)
        return [item for _score,item in scored[:limit]]

    def _discover_recommendation_seeds(self,limit:int=6):
        ds=self._discover_state(); seeds=[]; seen=set()
        def add(kind,ident,weight):
            try: tid=int(ident or 0)
            except Exception: return
            if tid<=0: return
            k=(kind,tid)
            if k in seen:return
            seen.add(k);seeds.append((kind,tid,weight))
        for rec in (ds.get('liked') or {}).values():
            if isinstance(rec,dict) and str(rec.get('provider') or '').lower()=='tmdb': add('tv' if rec.get('kind')=='tv' else 'movie',rec.get('metadata_id') or rec.get('tmdb_id'),4)
        for lib in reversed(self._library()):
            if str(lib.get('metadata_provider') or '').lower()=='tmdb' or lib.get('tmdb_id'): add('tv' if lib.get('kind')=='tv' else 'movie',lib.get('tmdb_id') or lib.get('metadata_id'),3)
        viewed=sorted((ds.get('viewed') or {}).values(),key=lambda x:float((x or {}).get('ts') or 0),reverse=True)
        for rec in viewed:
            if isinstance(rec,dict) and str(rec.get('provider') or '').lower()=='tmdb': add('tv' if rec.get('kind')=='tv' else 'movie',rec.get('metadata_id'),1)
        return seeds[:limit]

    def _discover_for_you(self,base_items:list[dict[str,Any]],limit:int=20,*,remote:bool=True):
        """Build personalized Discover rows without making the page depend on TMDB recommendations.

        The base Home feed is already useful recommendation material because it is ranked against
        the user's library/likes.  Remote TMDB recommendation calls are optional enrichment only.
        Keeping them bounded prevents a slow recommendation route from blocking Home or For You.
        """
        candidates=[]
        for x in base_items:
            y=dict(x); y['_recommend_weight']=0.4; candidates.append(y)
        if remote:
            # Four seeds fit in one worker wave.  A slow recommendation host can therefore add at
            # most ~4 seconds to the page instead of the old two 10-second waves (6 seeds / 4 workers).
            seeds=self._discover_recommendation_seeds(4)
            if seeds:
                with ThreadPoolExecutor(max_workers=min(4,len(seeds)),thread_name_prefix='discover-recommend') as pool:
                    jobs={pool.submit(self._metadata_api,f'/v1/recommendations/{kind}/{tid}',{'page':1},4):(kind,weight) for kind,tid,weight in seeds}
                    for fut in as_completed(jobs):
                        kind,weight=jobs[fut]
                        try:
                            data=fut.result()
                            for row in list((data or {}).get('results') or [])[:16]:
                                if isinstance(row,dict):
                                    item=self._proxy_summary(row,kind);item['_recommend_weight']=weight;candidates.append(item)
                        except Exception:
                            # Personalization is best effort.  The local/base ranking below still
                            # returns a useful For You page when TMDB recommendations are degraded.
                            pass
        return self._discover_recommend(self._discover_decorate(candidates),limit)

    @contextlib.contextmanager
    def _discover_refresh_process_guard(self, name:str):
        """Best-effort cross-process single-flight guard for Discover refreshes.

        Portable validation often has a desktop backend and background service alive at
        the same time. Both may share the same data/cache directory. A non-blocking
        one-byte lock keeps them from launching duplicate expensive Home/recommendation
        refreshes. Failure to acquire simply means another runtime is already warming
        the shared persistent cache.
        """
        path=self.data_dir / f'.discover-{re.sub(r"[^a-z0-9_-]+","-",str(name or "refresh").lower())}.lock'
        fh=None;acquired=False
        try:
            path.parent.mkdir(parents=True,exist_ok=True)
            fh=path.open('a+b')
            fh.seek(0,os.SEEK_END)
            if fh.tell()<=0:
                fh.write(b'0');fh.flush()
            fh.seek(0)
            try:
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(fh.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                acquired=True
            except OSError:
                acquired=False
            yield acquired
        finally:
            if acquired and fh is not None:
                try:
                    fh.seek(0)
                    if os.name=='nt':
                        import msvcrt
                        msvcrt.locking(fh.fileno(),msvcrt.LK_UNLCK,1)
                    else:
                        import fcntl
                        fcntl.flock(fh.fileno(),fcntl.LOCK_UN)
                except OSError:
                    pass
            if fh is not None:
                try: fh.close()
                except Exception: pass

    def _discover_home_cache_key(self) -> str:
        return 'cloud:'+self._metadata_service_base()+'/v1/discover/home'

    def _discover_refresh_home_worker(self):
        try:
            with self._discover_refresh_process_guard('home-refresh') as owner:
                if not owner:
                    return
                # Metadata Service v0.3.3 already bounds its individual TMDB sections.
                # Ten seconds gives that aggregate enough room without letting a refresh
                # monopolize a local NewzDeck request thread.
                data=self._metadata_api('/v1/discover/home',timeout=10)
                if isinstance(data,dict) and data.get('sections'):
                    with self.discover_home_cache_lock:
                        self.discover_home_cache=copy.deepcopy(data)
                        self.discover_home_cache_ts=time.monotonic()
        except Exception:
            # Stale Home data is preferable to replacing a working Discover page with
            # an error because one background refresh encountered a temporary outage.
            pass
        finally:
            with self.discover_home_refresh_lock:
                self.discover_home_refreshing=False

    def _start_discover_home_refresh(self):
        with self.discover_home_refresh_lock:
            if self.discover_home_refreshing:
                return False
            self.discover_home_refreshing=True
        threading.Thread(target=self._discover_refresh_home_worker,name='newzdeck-discover-home-refresh',daemon=True).start()
        return True

    def _discover_home_source(self, max_age:float=120.0, stale_age:int=12*3600):
        """Return Home immediately from a coherent cache and refresh in background.

        v3.5.25 still made the first request after the two-minute in-memory TTL wait for
        the hosted Home aggregate. That made Home/For You appear randomly slow whenever
        TMDB had a bad moment. v3.5.30 uses stale-while-revalidate: a recent memory or
        persistent cloud snapshot renders immediately, while one background worker
        refreshes it. Only a truly cold installation with no prior Home data waits.
        """
        now=time.monotonic()
        with self.discover_home_cache_lock:
            if isinstance(self.discover_home_cache,dict) and self.discover_home_cache.get('sections'):
                cached=copy.deepcopy(self.discover_home_cache)
                age=max(0.0,now-self.discover_home_cache_ts)
                if age>max_age:
                    self._start_discover_home_refresh()
                return cached

        # _metadata_api already persists successful cloud responses in metadata-cache.json.
        # Read that snapshot *before* making a network request so app restarts do not turn
        # a previously working Discover page back into a cold blocking load.
        persisted=self._cache_get(self._discover_home_cache_key(),stale_age)
        if isinstance(persisted,dict) and persisted.get('sections'):
            with self.discover_home_cache_lock:
                self.discover_home_cache=copy.deepcopy(persisted)
                # Mark it stale enough to trigger a background freshness check, but return
                # it immediately to the UI.
                self.discover_home_cache_ts=time.monotonic()-max_age-1.0
            self._start_discover_home_refresh()
            return copy.deepcopy(persisted)

        # True cold start: wait once, but for at most ten seconds. Any successful response
        # becomes both the normal metadata cache and the fast in-memory Home source.
        data=self._metadata_api('/v1/discover/home',timeout=10)
        if isinstance(data,dict) and data.get('sections'):
            with self.discover_home_cache_lock:
                self.discover_home_cache=copy.deepcopy(data)
                self.discover_home_cache_ts=time.monotonic()
        return data

    def _discover_taste_signature(self) -> str:
        ds=self._discover_state()
        libs=[]
        for item in self._library():
            if not isinstance(item,dict): continue
            libs.append((str(item.get('kind') or ''),str(item.get('tmdb_id') or item.get('metadata_id') or item.get('id') or ''),str(item.get('title') or '')))
        payload={
            'library':sorted(libs),
            'liked':sorted(str(k) for k in (ds.get('liked') or {}).keys()),
            'hidden':sorted(str(k) for k in (ds.get('hidden') or {}).keys()),
        }
        return hashlib.sha1(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()

    def _discover_refresh_for_you_worker(self, base_items:list[dict[str,Any]], limit:int, signature:str):
        try:
            with self._discover_refresh_process_guard('for-you-refresh') as owner:
                if not owner:
                    return
                enriched=self._discover_for_you(base_items,limit,remote=True)
                if enriched:
                    # Do not publish recommendations produced for an obsolete taste state.
                    if signature==self._discover_taste_signature():
                        with self.discover_for_you_cache_lock:
                            self.discover_for_you_cache=copy.deepcopy(enriched)
                            self.discover_for_you_cache_ts=time.monotonic()
                            self.discover_for_you_cache_signature=signature
                        self._cache_put('discover:for_you:'+signature,enriched)
        except Exception:
            pass
        finally:
            with self.discover_for_you_refresh_lock:
                self.discover_for_you_refreshing=False

    def _start_discover_for_you_refresh(self, base_items:list[dict[str,Any]], limit:int, signature:str):
        with self.discover_for_you_refresh_lock:
            if self.discover_for_you_refreshing:
                return False
            self.discover_for_you_refreshing=True
        threading.Thread(target=self._discover_refresh_for_you_worker,args=(copy.deepcopy(base_items),int(limit),str(signature)),name='newzdeck-discover-for-you-refresh',daemon=True).start()
        return True

    def _discover_for_you_fast(self, base_items:list[dict[str,Any]], limit:int=24):
        """Return personalized results without ever waiting on recommendation endpoints."""
        signature=self._discover_taste_signature()
        now=time.monotonic()
        with self.discover_for_you_cache_lock:
            if self.discover_for_you_cache_signature==signature and isinstance(self.discover_for_you_cache,list) and self.discover_for_you_cache:
                cached=copy.deepcopy(self.discover_for_you_cache[:limit])
                age=max(0.0,now-self.discover_for_you_cache_ts)
                if age>300:
                    self._start_discover_for_you_refresh(base_items,limit,signature)
                return cached

        persisted=self._cache_get('discover:for_you:'+signature,6*3600)
        if isinstance(persisted,list) and persisted:
            with self.discover_for_you_cache_lock:
                self.discover_for_you_cache=copy.deepcopy(persisted)
                self.discover_for_you_cache_signature=signature
                self.discover_for_you_cache_ts=time.monotonic()-301
            self._start_discover_for_you_refresh(base_items,limit,signature)
            return copy.deepcopy(persisted[:limit])

        # Local ranking is deterministic and fast. Start remote enrichment in the
        # background for the next render rather than keeping the current tab spinning.
        local=self._discover_for_you(base_items,limit,remote=False)
        self._start_discover_for_you_refresh(base_items,limit,signature)
        return local

    def discover_home(self, *, personalized:bool=False):
        try: data=self._discover_home_source()
        except Exception as exc: raise ValueError(f'TMDB Discover requires NewzDeck Metadata Service v0.2.0 or newer: {exc}') from exc
        sections=[self._discover_proxy_section(x) for x in list((data or {}).get('sections') or []) if isinstance(x,dict)]
        base=[item for section in sections[:5] for item in section.get('items') or []]

        # Home is local-only. For You returns local/cached personalized results immediately
        # and refreshes TMDB recommendation enrichment asynchronously for later renders.
        for_you=self._discover_for_you_fast(base,24) if personalized else self._discover_for_you(base,16,remote=False)
        if personalized:
            result_sections=[{'id':'for_you','title':'Recommended For You','subtitle':self._discover_section_subtitle('for_you'),'items':for_you}] if for_you else []
        else:
            result_sections=list(sections)
            if for_you:
                result_sections.insert(0,{'id':'for_you','title':'Recommended For You','subtitle':self._discover_section_subtitle('for_you'),'items':for_you})

        raw_featured=(data or {}).get('featured') if isinstance((data or {}).get('featured'),dict) else None
        featured=self._proxy_summary(raw_featured,raw_featured.get('media_type')) if raw_featured else None
        decorated=self._discover_decorate([featured] if featured else [])
        featured=(for_you[0] if personalized and for_you and for_you[0].get('backdrop_url') else (decorated[0] if decorated else (for_you[0] if for_you else None)))
        return {'featured':featured,'sections':result_sections,'errors':[],'sources':self.discover_sources(),'preferences':self.discover_preferences()}

    def discover_new(self):
        try:data=self._metadata_api('/v1/discover/new',timeout=20)
        except Exception as exc: raise ValueError(f'New Releases requires NewzDeck Metadata Service v0.2.0 or newer: {exc}') from exc
        sections=[self._discover_proxy_section(x) for x in list((data or {}).get('sections') or []) if isinstance(x,dict)]
        raw=(data or {}).get('featured') if isinstance((data or {}).get('featured'),dict) else None
        featured=self._proxy_summary(raw,raw.get('media_type')) if raw else None
        decorated=self._discover_decorate([featured] if featured else [])
        return {'featured':decorated[0] if decorated else None,'sections':sections,'errors':[],'sources':self.discover_sources(),'preferences':self.discover_preferences()}

    def discover_genres(self,kind:str):
        kind='tv' if str(kind).lower()=='tv' else 'movie'
        data=self._metadata_api(f'/v1/discover/genres/{kind}',timeout=10)
        return {'kind':kind,'genres':list((data or {}).get('genres') or [])}

    def discover_browse(self,data:dict[str,Any]):
        kind='tv' if str(data.get('kind') or '').lower()=='tv' else 'movie'; query=str(data.get('query') or '').strip()
        try: year=int(data.get('year') or 0)
        except Exception: year=0
        try:min_rating=float(data.get('min_rating')) if str(data.get('min_rating') or '').strip() else None
        except Exception:min_rating=None
        try:min_votes=int(data.get('min_votes') or 0) or None
        except Exception:min_votes=None
        genre_id=str(data.get('genre') or '').strip(); genre_name=str(data.get('genre_name') or '').strip(); language=str(data.get('language') or '').strip()
        sort=str(data.get('sort') or 'popularity'); release_type=str(data.get('release_type') or '').strip()
        try: page=max(1,min(250,int(data.get('page') or 1)))
        except Exception: page=1
        source_first=((page-1)*2)+1
        source_pages=(source_first,source_first+1)

        if query:
            blobs=[]
            for source_page in source_pages:
                try:
                    blobs.append(self._metadata_api('/v1/search',{'q':query,'type':kind,'year':year or None,'page':source_page},12))
                except Exception:
                    if not blobs: raise
                    break
            total=int((blobs[0] or {}).get('total_results') or 0) if blobs else 0
            rows=[]; seen=set()
            for blob in blobs:
                for raw in list((blob or {}).get('results') or []):
                    if not isinstance(raw,dict): continue
                    item=self._proxy_summary(raw,kind); key=str(item.get('tmdb_id') or '') or f"{_norm(item.get('title'))}:{item.get('year') or ''}"
                    if key in seen: continue
                    seen.add(key); rows.append(item)
            if genre_name: rows=[x for x in rows if genre_name.casefold() in {str(g).casefold() for g in x.get('genres') or []}]
            if min_rating is not None: rows=[x for x in rows if float(x.get('rating') or 0)>=min_rating]
            if language: rows=[x for x in rows if str(x.get('language') or '').lower()==language.lower()]
            if sort=='date_asc': rows.sort(key=lambda x:x.get('date') or '9999')
            elif sort=='date_desc': rows.sort(key=lambda x:x.get('date') or '',reverse=True)
            elif sort=='title_asc': rows.sort(key=lambda x:str(x.get('title') or '').casefold())
            elif sort=='title_desc': rows.sort(key=lambda x:str(x.get('title') or '').casefold(),reverse=True)
            elif sort=='rating': rows.sort(key=lambda x:(float(x.get('rating') or 0),int(x.get('vote_count') or 0)),reverse=True)
            else: rows.sort(key=lambda x:float(x.get('popularity') or 0),reverse=True)
            total_pages=max(1,min(250,(total+39)//40)) if total else 1
            return {'items':self._discover_decorate(rows[:40]),'sources':self.discover_sources(),'errors':[],'total_results':total or len(rows),'page':min(page,total_pages),'total_pages':total_pages,'page_size':40,'source_page_size':20}

        if kind=='movie':
            sort_map={'date_desc':'primary_release_date.desc','date_asc':'primary_release_date.asc','title_asc':'title.asc','title_desc':'title.desc','rating':'vote_average.desc','popularity':'popularity.desc'}
            common={'year':year or None,'sort_by':sort_map.get(sort,'popularity.desc'),'genres':genre_id or None,'min_rating':min_rating,'min_votes':min_votes,'release_type':release_type or None,'language':language or None,'region':'US'}
            path='/v1/discover/movies'
        else:
            sort_map={'date_desc':'first_air_date.desc','date_asc':'first_air_date.asc','title_asc':'name.asc','title_desc':'name.desc','rating':'vote_average.desc','popularity':'popularity.desc'}
            common={'year':year or None,'sort_by':sort_map.get(sort,'popularity.desc'),'genres':genre_id or None,'min_rating':min_rating,'min_votes':min_votes,'language':language or None}
            path='/v1/discover/tv'

        blobs=[]
        for source_page in source_pages:
            try: blobs.append(self._metadata_api(path,{**common,'page':source_page},15))
            except Exception:
                if not blobs: raise
                break
        first=blobs[0] if blobs else {}
        total=int((first or {}).get('total_results') or 0)
        source_total=max(1,int((first or {}).get('total_pages') or 1))
        available_source_pages=min(500,source_total)
        available_results=min(total,available_source_pages*20) if total else available_source_pages*20
        total_pages=max(1,(available_results+39)//40)
        rows=[]; seen=set()
        for blob in blobs:
            for raw in list((blob or {}).get('results') or []):
                if not isinstance(raw,dict): continue
                item=self._proxy_summary(raw,kind); key=str(item.get('tmdb_id') or '') or f"{_norm(item.get('title'))}:{item.get('year') or ''}"
                if key in seen: continue
                seen.add(key); rows.append(item)
        return {'items':self._discover_decorate(rows[:40]),'sources':self.discover_sources(),'errors':[],'page':min(page,total_pages),'total_pages':total_pages,'total_results':total,'page_size':40,'source_total_pages':source_total,'source_page_size':20}

    def _discover_proxy_detail(self,row:dict[str,Any],kind:str):
        item=self._proxy_summary(row,kind); ext=row.get('external_ids') if isinstance(row.get('external_ids'),dict) else {}
        images=row.get('images') if isinstance(row.get('images'),dict) else {}
        # Full-size artwork is reserved for the detail surface.  Grid/row cards use the TMDB
        # w500/w1280 variants so Chromium does not decode dozens of multi-megapixel originals.
        item['poster_url']=str(images.get('poster_original') or images.get('poster') or item.get('poster_url') or '')
        item['backdrop_url']=str(images.get('backdrop_original') or images.get('backdrop') or item.get('backdrop_url') or '')
        cast=[]
        for x in list(row.get('cast') or [])[:24]:
            cast.append({'tmdb_id':x.get('tmdb_id'),'name':str(x.get('name') or ''),'character':str(x.get('character') or ''),'image_url':str(x.get('profile') or '')})
        crew=[]
        for x in list(row.get('crew') or [])[:24]:
            crew.append({'tmdb_id':x.get('tmdb_id'),'name':str(x.get('name') or ''),'role':str(x.get('job') or x.get('department') or ''),'image_url':str(x.get('profile') or '')})
        videos=list(row.get('videos') or []); trailer=next((x for x in videos if str(x.get('type') or '').lower()=='trailer' and x.get('official')),None) or next((x for x in videos if str(x.get('type') or '').lower() in ('trailer','teaser')),None)
        next_ep=row.get('next_episode_to_air') if isinstance(row.get('next_episode_to_air'),dict) else {}
        last_ep=row.get('last_episode_to_air') if isinstance(row.get('last_episode_to_air'),dict) else {}
        item.update({'status':str(row.get('status') or ''),'runtime':row.get('runtime_minutes'),'official_site':str(row.get('homepage') or ''),'external_ids':ext,'imdb_id':str(ext.get('imdb') or ''),'tvdb_id':ext.get('tvdb'),'certification':str(row.get('certification') or ''),'companies':list(row.get('production_companies') or []),'networks':list(row.get('networks') or []),'network':str((row.get('networks') or [''])[0] if row.get('networks') else ''),'countries':list(row.get('countries') or []),'cast':cast,'crew':crew,'trailer_url':str((trailer or {}).get('url') or ''),'videos':videos,'recommendations':self._discover_decorate([self._proxy_summary(x,kind) for x in list(row.get('recommendations') or []) if isinstance(x,dict)]),'similar':self._discover_decorate([self._proxy_summary(x,kind) for x in list(row.get('similar') or []) if isinstance(x,dict)]),'number_of_seasons':row.get('number_of_seasons'),'number_of_episodes':row.get('number_of_episodes'),'seasons':list(row.get('seasons') or []),'theatrical_release_date':str(row.get('theatrical_release_date') or ''),'digital_release_date':str(row.get('digital_release_date') or ''),'physical_release_date':str(row.get('physical_release_date') or ''),'availability_date':str(row.get('availability_date') or ''),'next_episode':{'date':str(next_ep.get('air_date') or ''),'season':next_ep.get('season_number'),'episode':next_ep.get('episode_number'),'name':str(next_ep.get('name') or '')} if next_ep else None,'last_episode':{'date':str(last_ep.get('air_date') or ''),'season':last_ep.get('season_number'),'episode':last_ep.get('episode_number'),'name':str(last_ep.get('name') or '')} if last_ep else None,'attribution':{'source':'TMDB','license':'TMDB API Terms','url':f"https://www.themoviedb.org/{'tv' if kind=='tv' else 'movie'}/{item.get('tmdb_id') or ''}"}})
        return item

    def discover_detail(self,data:dict[str,Any]):
        kind='tv' if str(data.get('kind') or '').lower()=='tv' else 'movie'; ident=str(data.get('metadata_id') or data.get('tmdb_id') or '').strip(); provider=str(data.get('provider') or 'tmdb').lower()
        if provider!='tmdb' or not ident.isdigit():
            title=str(data.get('title') or '').strip(); year=int(data.get('year') or 0) if str(data.get('year') or '').isdigit() else None
            matches=self._metadata_service_search(kind,title,year)
            exact=[x for x in matches if _norm(x.get('title'))==_norm(title) and (not year or not x.get('year') or int(x.get('year'))==year)]
            if not exact: raise ValueError('TMDB title could not be resolved')
            ident=str(exact[0].get('tmdb_id') or '')
        detail_key=f'{kind}:{int(ident)}'; row=None; now=time.monotonic()
        with self.discover_detail_cache_lock:
            cached=self.discover_detail_cache.get(detail_key)
            if cached and now-float(cached[0])<600:
                row=copy.deepcopy(cached[1])
        if row is None:
            row=self._metadata_api(f'/v1/{kind}/{int(ident)}',timeout=18)
            if isinstance(row,dict):
                with self.discover_detail_cache_lock:
                    self.discover_detail_cache[detail_key]=(time.monotonic(),copy.deepcopy(row))
                    if len(self.discover_detail_cache)>80:
                        oldest=sorted(self.discover_detail_cache.items(),key=lambda kv:kv[1][0])[:20]
                        for key,_ in oldest:self.discover_detail_cache.pop(key,None)
        item=self._discover_proxy_detail(row,kind); decorated=self._discover_decorate([item]); item=decorated[0] if decorated else item
        st=self._discover_state(); st['viewed'][self._discover_key(item)]={'ts':time.time(),'provider':'tmdb','metadata_id':str(item.get('metadata_id') or ''),'kind':kind,'title':item.get('title'),'year':item.get('year')}; self._save_discover_state(st)
        return {'item':item,'sources':self.discover_sources()}

    def discover_person(self,data:dict[str,Any]):
        ident=str(data.get('tmdb_id') or data.get('metadata_id') or '').strip()
        if not ident.isdigit(): raise ValueError('TMDB person identifier is required')
        raw=self._metadata_api(f'/v1/person/{int(ident)}',timeout=15)
        credits=[]
        for row in list((raw or {}).get('credits') or []):
            if isinstance(row,dict) and str(row.get('media_type') or '') in ('movie','tv'):
                x=self._proxy_summary(row,str(row.get('media_type')));x['character']=str(row.get('character') or '');credits.append(x)
        return {'person':{'tmdb_id':int(ident),'name':str((raw or {}).get('name') or ''),'biography':str((raw or {}).get('biography') or ''),'birthday':str((raw or {}).get('birthday') or ''),'deathday':str((raw or {}).get('deathday') or ''),'place_of_birth':str((raw or {}).get('place_of_birth') or ''),'department':str((raw or {}).get('known_for_department') or ''),'profile_url':str((raw or {}).get('profile') or ''),'homepage':str((raw or {}).get('homepage') or ''),'credits':self._discover_decorate(credits)},'sources':self.discover_sources()}

    def discover_preference(self,data:dict[str,Any]):
        action=str(data.get('action') or '').lower(); item=data.get('item') if isinstance(data.get('item'),dict) else {}; key=self._discover_key(item)
        if not key or key.startswith('::'): raise ValueError('Discover item is invalid')
        st=self._discover_state(); snapshot={k:item.get(k) for k in ('provider','metadata_id','tmdb_id','kind','title','year','genres','poster_url')}
        if action=='like': st['liked'][key]=snapshot;st['hidden'].pop(key,None)
        elif action in ('hide','not_interested'):st['hidden'][key]=snapshot;st['liked'].pop(key,None)
        elif action in ('clear','neutral'):st['liked'].pop(key,None);st['hidden'].pop(key,None)
        else:raise ValueError('Unknown Discover preference action')
        self._save_discover_state(st);return {'ok':True,'preferences':self.discover_preferences()}

    def discover_preferences(self):
        st=self._discover_state();return {'liked':list((st.get('liked') or {}).keys()),'hidden':list((st.get('hidden') or {}).keys()),'viewed_count':len(st.get('viewed') or {})}

    def discover_sources(self):
        return [{'name':'TMDB','purpose':'Movies, TV, posters, backdrops, people, trending, recommendations and release metadata','license':'TMDB API terms / non-commercial developer access','url':'https://www.themoviedb.org'}]

    def discover_search_releases(self,data:dict[str,Any]):
        kind='tv' if str(data.get('kind') or '').lower()=='tv' else 'movie'; title=str(data.get('title') or '').strip()
        if not title:raise ValueError('A title is required')
        year=int(data.get('year') or 0) if str(data.get('year') or '').isdigit() else None
        tmdb_id=int(data.get('tmdb_id') or data.get('metadata_id') or 0) if str(data.get('tmdb_id') or data.get('metadata_id') or '').isdigit() else None
        provider=str(data.get('provider') or ('tmdb' if tmdb_id else '')).strip().lower()
        requested_profile=str(data.get('quality_profile_id') or '').strip(); profiles=self._profiles(); profile=next((p for p in profiles if str(p.get('id') or '')==requested_profile),profiles[0])
        requested_root=str(data.get('root_folder') or '').strip()
        temp={'kind':kind,'title':title,'year':year,'tmdb_id':tmdb_id,'metadata_id':tmdb_id,'provider':provider,'root_folder':requested_root,'quality_profile_id':str(profile.get('id') or '')}
        releases=[];errors=[];enabled=[idx for idx in self._indexers() if idx.get('enabled',True)]
        if enabled:
            pool=ThreadPoolExecutor(max_workers=min(12,len(enabled)),thread_name_prefix='newznab-discover')
            jobs={pool.submit(self._search_indexer,idx,temp,None,None):idx for idx in enabled}
            done,pending=wait(jobs,timeout=_indexer_search_wall_timeout())
            for fut in done:
                idx=jobs[fut]
                try:
                    for r in fut.result():
                        if not _slug_match(str(r.get('title') or ''),title,year if kind=='movie' else None):
                            continue
                        score,info,reasons,accepted=self._score_release(r['title'],r['size'],profile)
                        r.update({'score':score,'parsed':info,'reasons':reasons,'accepted':accepted,'item_id':'','media_kind':kind,'media_title':title,'media_year':year,'media_tmdb_id':tmdb_id,'media_provider':provider,'media_root_folder':requested_root,'media_quality_profile_id':str(profile.get('id') or ''),'season':info.get('season'),'episode':info.get('episode'),'season_pack':bool(info.get('is_season_pack')),'episode_title':''});releases.append(r)
                except Exception as exc:errors.append({'indexer':idx.get('name'),'error':str(exc)})
            for fut in pending:
                idx=jobs[fut]; fut.cancel(); errors.append({'indexer':idx.get('name'),'error':f'Timed out after {_indexer_search_wall_timeout():g} seconds; other indexer results were returned without waiting.'})
            pool.shutdown(wait=False,cancel_futures=True)
        unique={}
        for r in releases:
            key=(r.get('guid') or r.get('title','')).casefold();old=unique.get(key)
            if old is None or int(r.get('score',0))>int(old.get('score',0)):unique[key]=r
        rows=sorted(unique.values(),key=lambda x:(bool(x.get('accepted')),int(x.get('score',-9999)),int(x.get('published',0))),reverse=True)
        return {'item':temp,'profile':profile,'releases':rows[:300],'errors':errors,'searched_indexers':len(enabled)}

    def _profile_id(self, pid=''):
        profiles=self._profiles(); ids={str(p.get('id')) for p in profiles}; return pid if pid in ids else str(profiles[0].get('id'))

    def add_media(self,data:dict[str,Any]):
        kind='tv' if str(data.get('kind')).lower()=='tv' else 'movie'
        provider=str(data.get('provider') or '').strip().lower()
        metadata_id=str(data.get('metadata_id') or data.get('tvmaze_id') or data.get('wikidata_id') or '').strip()
        tmdb_id=str(data.get('tmdb_id') or '').strip()
        if not provider and tmdb_id: provider='tmdb'; metadata_id=tmdb_id
        title=str(data.get('title') or '').strip(); year=data.get('year')
        default_mode='all' if kind=='tv' else 'movie'
        allowed_modes={'all','future','missing','none'} if kind=='tv' else {'movie','missing','none'}
        monitor_mode=str(data.get('monitor_mode') or default_mode).strip().lower()
        if monitor_mode not in allowed_modes: monitor_mode=default_mode
        monitored=bool(data.get('monitored',monitor_mode!='none')) and monitor_mode!='none'
        requested_library_title=_safe_component(data.get('library_title'),'') if kind=='tv' and str(data.get('library_title') or '').strip() else ''
        item={'id':secrets.token_hex(8),'kind':kind,'title':title or 'Untitled','year':int(year) if str(year or '').isdigit() else None,'metadata_provider':provider,'metadata_id':metadata_id or None,'tvmaze_id':int(metadata_id) if provider=='tvmaze' and metadata_id.isdigit() else None,'wikidata_id':metadata_id.upper() if provider=='wikidata' and re.fullmatch(r'Q\d+',metadata_id,re.I) else None,'tmdb_id':int(tmdb_id) if tmdb_id.isdigit() else None,'poster_url':str(data.get('poster_url') or ''),'overview':str(data.get('overview') or ''),'genres':list(data.get('genres') or []),'rating':data.get('rating'),'network':str(data.get('network') or ''),'status':str(data.get('status') or 'unknown'),'monitored':monitored,'monitor_mode':monitor_mode,'quality_profile_id':self._profile_id(str(data.get('quality_profile_id') or '')),'root_folder':str(data.get('root_folder') or ''),'added_at':_now(),'updated_at':_now(),'seasons':[],'movie_file':None}
        if requested_library_title:
            item['library_title']=requested_library_title; item['library_title_source']='manual'

        if provider=='tvmaze' and item.get('tvmaze_id'):
            show_id=int(item['tvmaze_id'])
            d=self._tvmaze(f'shows/{show_id}',{},21600)
            date=_date(d.get('premiered')); image=d.get('image') or {}
            item.update({'title':str(d.get('name') or item['title']),'overview':self._strip_html(d.get('summary')),'first_air_date':date,'year':int(date[:4]) if date[:4].isdigit() else item['year'],'status':str(d.get('status') or 'Unknown'),'poster_url':str(image.get('original') or image.get('medium') or item['poster_url']),'external_ids':d.get('externals') or {},'genres':list(d.get('genres') or []),'rating':(d.get('rating') or {}).get('average'),'network':str(((d.get('webChannel') or d.get('network') or {}).get('name')) or ''),'language':str(d.get('language') or '')})
            episodes=self._tvmaze(f'shows/{show_id}/episodes',{'specials':'1'},21600)
            seasons_by={}
            for ep in list(episodes or []):
                sn=int(ep.get('season') or 0); en=int(ep.get('number') or 0)
                if sn<=0 or en<=0: continue
                air=_date(ep.get('airdate'))
                seasons_by.setdefault(sn,[]).append({'episode_number':en,'name':str(ep.get('name') or f'Episode {en}'),'air_date':air,'overview':self._strip_html(ep.get('summary')),'monitored':True,'has_file':False,'file_path':'','file_quality':'','cutoff_met':False,'tvmaze_episode_id':ep.get('id')})
            item['seasons']=[{'season_number':sn,'name':f'Season {sn}','air_date':min([e.get('air_date') for e in eps if e.get('air_date')] or ['']),'monitored':True,'episodes':sorted(eps,key=lambda e:int(e.get('episode_number') or 0))} for sn,eps in sorted(seasons_by.items())]

        elif provider=='wikidata' and item.get('wikidata_id'):
            d=self._movie_from_entity(self._wikidata_movie_entity(str(item['wikidata_id'])),True)
            item.update({'title':str(d.get('title') or item['title']),'overview':str(d.get('overview') or item['overview']),'release_date':_date(d.get('release_date')),'year':d.get('year') or item['year'],'status':'Released' if d.get('release_date') else 'Unknown','poster_url':str(d.get('poster_url') or item['poster_url']),'runtime':d.get('runtime'),'imdb_id':str(d.get('imdb_id') or ''),'wikipedia_title':str(d.get('wikipedia_title') or '')})

        elif provider=='tmdb' and item.get('tmdb_id'):
            if kind=='movie':
                self._apply_tmdb_movie(item,self._metadata_movie_detail(int(item['tmdb_id'])))
            else:
                self._apply_tmdb_tv(item,self._metadata_tv_bundle(int(item['tmdb_id'])))
                if not requested_library_title: self._refresh_tv_library_identity(item,allow_network=True)
            item['metadata_refreshed_at']=_now()
        elif kind=='tv' and not requested_library_title:
            item['library_title']=self._tv_default_library_title(item); item['library_title_source']='auto'

        with self.lock:
            lib=self._library()
            for existing in lib:
                if metadata_id and existing.get('kind')==kind and str(existing.get('metadata_provider') or '').lower()==provider and str(existing.get('metadata_id') or '')==metadata_id:
                    raise ValueError('That title is already in your NewzDeck library')
                if item.get('tmdb_id') and existing.get('kind')==kind and existing.get('tmdb_id')==item.get('tmdb_id'):
                    raise ValueError('That title is already in your NewzDeck library')
                if not metadata_id and not item.get('tmdb_id') and existing.get('kind')==kind and _norm(existing.get('title'))==_norm(item.get('title')) and existing.get('year')==item.get('year'):
                    raise ValueError('That title is already in your NewzDeck library')
            lib.append(item); self._save_library(lib); self._event('library',f"Added {item['title']}",item_id=str(item.get('id') or ''),media_kind=kind,metadata_provider=provider or 'manual')
        return item

    def update_media(self,data:dict[str,Any]):
        ident=str(data.get('id') or '')
        with self.lock:
            lib=self._library(); item=next((x for x in lib if str(x.get('id'))==ident),None)
            if not item: raise ValueError('Library item was not found')
            for k in ('monitored','quality_profile_id','root_folder'):
                if k in data: item[k]=data[k]
            if item.get('kind')=='tv' and 'library_title' in data:
                requested=str(data.get('library_title') or '').strip()
                if requested:
                    item['library_title']=_safe_component(requested,str(item.get('title') or 'TV Show')); item['library_title_source']='manual'
                else:
                    item.pop('library_title',None); item['library_title_source']='auto'; self._refresh_tv_library_identity(item,allow_network=False)
            if 'monitor_mode' in data:
                kind='tv' if item.get('kind')=='tv' else 'movie'; default_mode='all' if kind=='tv' else 'movie'; allowed={'all','future','missing','none'} if kind=='tv' else {'movie','missing','none'}
                mode=str(data.get('monitor_mode') or default_mode).strip().lower(); mode=mode if mode in allowed else default_mode; item['monitor_mode']=mode
                if 'monitored' not in data: item['monitored']=mode!='none'
                if mode=='none': item['monitored']=False
            if item.get('kind')=='tv' and 'monitor_mode' in data:
                mode=str(item.get('monitor_mode') or 'all')
                today=datetime.now().date().isoformat()
                for season in item.get('seasons') or []:
                    for ep in season.get('episodes') or []:
                        if mode=='none': ep['monitored']=False
                        elif mode=='future': ep['monitored']=bool(ep.get('air_date') and str(ep.get('air_date'))>=today)
                        elif mode=='missing': ep['monitored']=not bool(ep.get('has_file'))
                        else: ep['monitored']=True
                    season['monitored']=any(bool(ep.get('monitored',True)) for ep in season.get('episodes') or []) if season.get('episodes') else mode!='none'
            if 'season_number' in data:
                sn=int(data.get('season_number') or 0)
                s=next((x for x in item.get('seasons',[]) if int(x.get('season_number',0))==sn),None)
                if s and 'season_monitored' in data:
                    s['monitored']=bool(data['season_monitored'])
                    for ep in s.get('episodes',[]): ep['monitored']=bool(data['season_monitored'])
            if 'episode_number' in data and 'season_number' in data:
                sn,en=int(data.get('season_number') or 0),int(data.get('episode_number') or 0)
                s=next((x for x in item.get('seasons',[]) if int(x.get('season_number',0))==sn),None)
                ep=next((x for x in (s or {}).get('episodes',[]) if int(x.get('episode_number',0))==en),None)
                if ep and 'episode_monitored' in data: ep['monitored']=bool(data['episode_monitored'])
            item['updated_at']=_now(); self._save_library(lib); return item

    def media_location(self,ident:str) -> str:
        item=next((x for x in self._library() if str(x.get('id'))==str(ident)),None)
        if not item: raise ValueError('Library item was not found')
        root=self._resolve_root(item)
        if not root: raise ValueError('No Root Folder is configured for this title')
        if item.get('kind')=='tv':
            existing=self._existing_tv_series_folder(item,root)
            if existing is not None: return str(existing)
            values={'title':str(item.get('title') or 'TV Show'),'year':item.get('year') or '','library_title':self._tv_library_title(item)}
            candidate=self._tv_series_folder(item,root,self._config(),values)
            if candidate.exists() and candidate.is_dir(): return str(candidate)
            return str(root)
        existing=self._existing_media_path(item)
        if existing and existing.exists(): return str(existing.parent)
        return str(root)

    def refresh_media_metadata(self,ident:str):
        if not any(str(x.get('id'))==str(ident) for x in self._library()): raise ValueError('Library item was not found')
        return self.refresh_monitored_metadata(force=True,ident=str(ident))

    def delete_media(self,ident:str):
        with self.lock:
            lib=self._library(); before=len(lib); lib=[x for x in lib if str(x.get('id'))!=str(ident)]
            if len(lib)==before: raise ValueError('Library item was not found')
            self._save_library(lib); return {'ok':True}

    def _media_quality_cache(self) -> dict[str,Any]:
        value=_read(self.media_quality_cache_file,{})
        return value if isinstance(value,dict) else {}

    def _media_fingerprint(self, path: Path) -> str:
        """Stable, cheap identity for a media file that survives a rename/move."""
        try:
            st=path.stat(); size=int(st.st_size)
            h=hashlib.sha256(); h.update(str(size).encode('ascii'))
            chunk=128*1024
            with path.open('rb') as f:
                h.update(f.read(chunk))
                if size>chunk:
                    f.seek(max(0,size-chunk)); h.update(f.read(chunk))
            return f'{size}:{h.hexdigest()[:32]}'
        except OSError:
            return ''

    def _probe_media_resolution(self, path: Path) -> str:
        """Best-effort container probe without requiring FFmpeg/MediaInfo.

        NewzDeck's own imports retain the exact release quality in the fingerprint
        cache. This probe is the fallback for pre-existing/user-renamed media and is
        intentionally limited to resolution, which can be established from the file
        itself even when WEB-DL/BluRay source metadata is no longer present.
        """
        def label(w:int,h:int) -> str:
            edge=max(int(w or 0),int(h or 0)); short=min(int(w or 0),int(h or 0))
            if edge>=3000 or short>=1700: return '2160p'
            if edge>=1600 or short>=900: return '1080p'
            if edge>=1100 or short>=650: return '720p'
            if edge>=850 or short>=520: return '576p'
            if edge>=600 or short>=350: return '480p'
            return 'Unknown'
        try:
            suffix=path.suffix.casefold()
            with path.open('rb') as f: data=f.read(8*1024*1024)

            if suffix in {'.mkv','.webm'}:
                vals=[]
                for marker in (0xB0,0xBA):
                    found=[]; start=0
                    while True:
                        i=data.find(bytes([marker]),start)
                        if i<0: break
                        start=i+1
                        if i+2>=len(data): continue
                        first=data[i+1]
                        mask=0x80; n=1
                        while n<=8 and not (first & mask): mask >>= 1; n += 1
                        if n>4 or i+1+n>=len(data): continue
                        size=first & (mask-1)
                        for b in data[i+2:i+1+n]: size=(size<<8)|b
                        if size<1 or size>4 or i+1+n+size>len(data): continue
                        value=int.from_bytes(data[i+1+n:i+1+n+size],'big')
                        if 200<=value<=10000: found.append((i,value))
                    vals.append(found)
                for wi,w in vals[0]:
                    for hi,h in vals[1]:
                        if abs(wi-hi)<=2048:
                            q=label(w,h)
                            if q!='Unknown': return q

            if suffix in {'.mp4','.m4v','.mov'}:
                for typ in (b'avc1',b'hvc1',b'hev1',b'av01',b'mp4v'):
                    start=0
                    while True:
                        i=data.find(typ,start)
                        if i<0: break
                        start=i+4
                        if i+32>len(data): continue
                        w=int.from_bytes(data[i+28:i+30],'big'); h=int.from_bytes(data[i+30:i+32],'big')
                        if 200<=w<=10000 and 200<=h<=10000:
                            q=label(w,h)
                            if q!='Unknown': return q
        except OSError:
            pass
        return 'Unknown'

    def _probe_media_traits(self, path: Path) -> dict[str,Any]:
        """Best-effort codec/HDR/audio inspection using container signatures only.

        Exact release source (WEB-DL/BluRay/etc.) is preserved from NewzDeck's
        import fingerprint record. These traits are intentionally conservative and
        never manufacture source metadata from the container.
        """
        info={'resolution':self._probe_media_resolution(path),'video_codec':'Unknown','hdr':'Unknown','audio_codec':'Unknown'}
        try:
            size=int(path.stat().st_size); span=12*1024*1024
            with path.open('rb') as f:
                head=f.read(span)
                tail=b''
                if size>span:
                    f.seek(max(0,size-span)); tail=f.read(span)
            data=(head+tail).lower()
            suffix=path.suffix.casefold()
            if suffix in {'.mkv','.webm'}:
                if b'v_mpegh/iso/hevc' in data: info['video_codec']='HEVC/x265'
                elif b'v_mpeg4/iso/avc' in data: info['video_codec']='AVC/x264'
                elif b'v_av1' in data: info['video_codec']='AV1'
                if b'a_truehd' in data: info['audio_codec']='TrueHD'
                elif b'a_eac3' in data: info['audio_codec']='DD+'
                elif b'a_ac3' in data: info['audio_codec']='AC3'
                elif b'a_dts' in data: info['audio_codec']='DTS'
                elif b'a_aac' in data: info['audio_codec']='AAC'
            elif suffix in {'.mp4','.m4v','.mov'}:
                if b'av01' in data: info['video_codec']='AV1'
                elif b'hvc1' in data or b'hev1' in data: info['video_codec']='HEVC/x265'
                elif b'avc1' in data: info['video_codec']='AVC/x264'
                if b'mlpa' in data: info['audio_codec']='TrueHD'
                elif b'ec-3' in data: info['audio_codec']='DD+'
                elif b'ac-3' in data: info['audio_codec']='AC3'
                elif any(x in data for x in (b'dtsh',b'dtsl',b'dtsc')): info['audio_codec']='DTS'
                elif b'mp4a' in data: info['audio_codec']='AAC'
            if any(x in data for x in (b'dvhe',b'dvh1',b'dovi',b'dolby vision')): info['hdr']='Dolby Vision'
            elif b'hdr10+' in data or b'stmp' in data: info['hdr']='HDR10+'
            elif any(x in data for x in (b'masteringmetadata',b'maxcll',b'smpte2086',b'bt2020')): info['hdr']='HDR/HDR10'
        except OSError:
            pass
        return info

    def _disk_free(self, path:Path|None) -> int:
        if not path: return 0
        try:
            probe=path
            while not probe.exists() and probe.parent!=probe: probe=probe.parent
            return int(shutil.disk_usage(probe).free)
        except OSError:
            return 0

    def _storage_requirement(self, release_size:int, *, staging:bool=False) -> int:
        size=max(0,int(release_size or 0)); reserve=max(1,int(self.public_config().get('automatic_storage_reserve_gb') or 5))*1024**3

        multiplier=2.20 if staging else 1.10
        return reserve + int(size*multiplier)

    def _existing_media_path(self,item:dict[str,Any]) -> Path|None:
        raw=''
        if item.get('kind')=='movie': raw=str((item.get('movie_file') or {}).get('path') or '')
        else:
            for season in item.get('seasons') or []:
                for ep in season.get('episodes') or []:
                    if ep.get('has_file') and ep.get('file_path'):
                        raw=str(ep.get('file_path')); break
                if raw: break
        return Path(raw) if raw else None

    def _existing_tv_series_folder(self, item:dict[str,Any], root:Path|None=None) -> Path|None:
        """Return an established series directory without confusing it with a season folder.

        Title-level Open Folder and Smart Import used to derive their location from the
        first existing episode.  Because that path ends in e.g. ``Season 2\file.mkv``,
        the UI opened Season 2 and imports could ignore an existing custom series folder.
        Prefer the actual series directory already represented by library files, but only
        when it belongs to the currently configured root.
        """
        candidates=[]
        for season in item.get('seasons') or []:
            for ep in season.get('episodes') or []:
                raw=str(ep.get('file_path') or '').strip()
                if not raw: continue
                path=Path(raw)
                parent=path.parent
                if re.fullmatch(r'(?i)(?:season|series)[ ._-]*\d{1,3}|specials?', parent.name or ''):
                    parent=parent.parent
                if root is not None:
                    try:
                        parent.resolve().relative_to(root.resolve())
                    except (OSError,ValueError):
                        continue
                if parent.exists() and parent.is_dir(): candidates.append(parent)
        if not candidates: return None
        counts={}
        for path in candidates:
            try: key=str(path.resolve()).casefold()
            except OSError: key=str(path).casefold()
            rec=counts.setdefault(key,[0,path]); rec[0]+=1
        return max(counts.values(),key=lambda x:x[0])[1]

    def _tv_series_folder(self, item:dict[str,Any], root:Path, cfg:dict[str,Any], values:dict[str,Any]) -> Path:
        desired=_safe_component(values.get('library_title') or item.get('library_title') or '','')
        if desired:
            direct=root/desired
            if direct.exists() and direct.is_dir(): return direct
            try:
                for child in root.iterdir():
                    if child.is_dir() and child.name.casefold()==desired.casefold(): return child
            except OSError: pass
        existing=self._existing_tv_series_folder(item,root)
        if existing is not None: return existing
        title=str(item.get('title') or values.get('title') or 'TV Show'); year=item.get('year') or values.get('year') or ''
        library_title=str(values.get('library_title') or self._tv_library_title(item) or (f'{title} ({year})' if year else title))
        values=dict(values); values['library_title']=library_title
        folder=self._template(str(cfg.get('tv_folder_template') or '{library_title}'),values,_safe_component(library_title,title))
        return root/folder

    def _quality_for_media(self, path: Path, cache:dict[str,Any], previous:dict[str,Any]|None=None) -> tuple[str,str,str,bool]:
        """Return quality, source-of-truth, fingerprint, cache_changed."""
        size=0
        try: size=int(path.stat().st_size)
        except OSError: pass
        prev=previous if isinstance(previous,dict) else {}
        prev_q=str(prev.get('file_quality') or prev.get('quality') or '')
        prev_path=str(prev.get('file_path') or prev.get('path') or '')
        prev_size=int(prev.get('file_size') or prev.get('size') or 0)
        if prev_q and prev_q!='Unknown' and prev_path and Path(prev_path)==path and (not prev_size or prev_size==size):
            fp=str(prev.get('file_fingerprint') or '') or self._media_fingerprint(path)
            return prev_q,str(prev.get('quality_source') or 'library-record'),fp,False
        fp=self._media_fingerprint(path)
        rec=cache.get(fp) if fp else None
        if isinstance(rec,dict) and str(rec.get('quality') or '') not in {'','Unknown'}:
            return str(rec.get('quality')),str(rec.get('source') or 'fingerprint-cache'),fp,False
        parsed=parse_release(path.name)
        if str(parsed.get('quality') or '')!='Unknown':
            q=str(parsed.get('quality')); changed=False
            if fp:
                cache[fp]={'quality':q,'source':'filename','release_title':path.name,'updated_at':_now()}; changed=True
            return q,'filename',fp,changed
        resolution=self._probe_media_resolution(path)
        if resolution!='Unknown':
            return f'{resolution} Unknown','media-probe',fp,False
        return 'Unknown','unknown',fp,False

    def _remember_media_quality(self, path: Path, quality:str, release_title:str='') -> str:
        fp=self._media_fingerprint(path)
        if not fp or not quality or quality=='Unknown': return fp
        cache=self._media_quality_cache()
        cache[fp]={'quality':str(quality),'source':'newzdeck-import','release_title':str(release_title or ''),'updated_at':_now(),'path_hint':str(path)}
        if len(cache)>10000:
            rows=sorted(cache.items(),key=lambda kv:str((kv[1] or {}).get('updated_at') or ''),reverse=True)[:8000]; cache=dict(rows)
        _write(self.media_quality_cache_file,cache)
        return fp

    def _quality_cutoff_met(self, quality:str, profile:dict[str,Any]) -> bool:
        rank=self._quality_rank(quality,profile); cutoff=self._quality_rank(str(profile.get('cutoff') or ''),profile)
        if rank<999 and cutoff<999: return rank<=cutoff


        def res(q):
            m=re.search(r'(?i)\b(2160|1080|720|576|480)p\b',str(q or ''))
            return int(m.group(1)) if m else 0
        current,goal=res(quality),res(profile.get('cutoff'))
        return bool(current and goal and current>=goal)

    def _quality_rank(self, quality:str, profile:dict[str,Any]):
        vals=list(profile.get('qualities') or [])

        def profile_key(value:Any) -> str:
            q=_norm(value)
            m=re.fullmatch(r'(2160p|1080p|720p|576p|480p) web',q)
            if m:
                return f'{m.group(1)} web dl'
            return q

        q=profile_key(quality)
        for i,v in enumerate(vals):
            if profile_key(v)==q: return i
        return 999

    def _evaluate_release(self, title:str, size:int, profile:dict[str,Any], *, item:dict[str,Any]|None=None, season=None, episode=None, current_quality:str='Unknown') -> dict[str,Any]:
        """Explain and score a release using one shared decision model."""
        info=parse_release(title); reasons=[]; components=[]; rejects=[]; score=0
        raw=str(title or ''); low=' '+_norm(raw)+' '
        rank=self._quality_rank(info.get('quality'),profile)
        if rank<999:
            qpts=max(12,60-rank*6); score+=qpts; components.append({'label':f"Quality • {info.get('quality')}",'score':qpts}); reasons.append(f"{info.get('quality')} is profile rank #{rank+1}")
        else: rejects.append(f"{info.get('quality') or 'Unknown quality'} is outside the quality profile")
        if item:
            wanted_title=str(item.get('title') or '')
            if _slug_match(raw,wanted_title,item.get('year') if item.get('kind')=='movie' else None):
                score+=20; components.append({'label':'Title match','score':20}); reasons.append('Title matches library item')
            else: rejects.append('Title/year does not safely match the library item')
            if item.get('kind')=='movie' and item.get('year'):
                years=re.findall(r'\b(?:19|20)\d{2}\b',raw)
                if str(item.get('year')) in years:
                    score+=8; components.append({'label':'Year match','score':8}); reasons.append(f"Year {item.get('year')} matches")
                elif years: rejects.append(f"Release year {years[0]} does not match {item.get('year')}")
            elif item.get('kind')=='tv' and season is not None:
                try: sn=int(season)
                except Exception: sn=0
                if episode is None:
                    if int(info.get('season') or 0)==sn and bool(info.get('is_season_pack')):
                        score+=20; components.append({'label':f'Season {sn} pack match','score':20}); reasons.append('Complete/bare-season release matches the requested season pack')
                    else: rejects.append(f'Release is not a safe Season {sn} pack')
                else:
                    try: en=int(episode)
                    except Exception: en=0
                    if int(info.get('season') or 0)==sn and int(info.get('episode') or 0)==en:
                        score+=15; components.append({'label':f'S{sn:02d}E{en:02d} match','score':15}); reasons.append('Exact episode match')
                    else: rejects.append(f"Release does not match S{sn:02d}E{en:02d}")
                    if bool(info.get('is_multi_episode')): rejects.append('Multi-episode release requires an explicit multi-episode importer')
                    if bool(info.get('is_season_pack')): rejects.append('Season pack should be searched/imported at the season level')
        safety=re.search(r'(?i)(?:^|[ ._\-])(sample|trailer|proof|extras?|password(?:ed)?|encrypted|repair[ ._\-]*only)(?:[ ._\-]|$)',raw)
        if safety: rejects.append(f"Unsafe/non-feature marker detected: {safety.group(1)}")
        reject_terms=[_norm(x) for x in profile.get('reject_terms') or [] if _norm(x)]
        for term in reject_terms:
            if term in low: rejects.append(f"Profile rejection term matched: {term}")
        min_mb=max(0,float(profile.get('min_size_mb') or 0)); max_gb=max(0,float(profile.get('max_size_gb') or 0))
        if size>0:
            size_mb=size/1024**2; size_gb=size/1024**3
            if min_mb and size_mb<min_mb: rejects.append(f"Size {size_mb:.0f} MB is below profile minimum {min_mb:.0f} MB")
            if max_gb and size_gb>max_gb: rejects.append(f"Size {size_gb:.1f} GB exceeds profile maximum {max_gb:.1f} GB")
            score+=2; components.append({'label':'Indexer size reported','score':2})
        else: reasons.append('Indexer did not report size')
        for cf in profile.get('custom_formats') or []:
            terms=[_norm(x) for x in cf.get('contains') or [] if _norm(x)]
            if terms and any(t in low for t in terms):
                val=int(cf.get('score',0) or 0); score+=val; components.append({'label':str(cf.get('name') or 'Preference'),'score':val}); reasons.append(f"{cf.get('name','Preference')} {val:+d}")
        group=str(info.get('release_group') or '').casefold(); preferred={str(x or '').strip().casefold() for x in profile.get('preferred_groups') or [] if str(x or '').strip()}
        if group and group in preferred:
            score+=12; components.append({'label':f"Preferred group • {info.get('release_group')}",'score':12}); reasons.append(f"Preferred release group {info.get('release_group')}")
        if re.search(r'(?i)(?:^|[ ._\-])(proper|repack)(?:[ ._\-]|$)',raw):
            score+=6; components.append({'label':'PROPER / REPACK','score':6}); reasons.append('PROPER/REPACK bonus')
        if str(info.get('source') or '')=='WEB' and rank<999:
            reasons.append('Generic WEB tag is treated as WEB-DL-compatible for this quality profile')
        elif str(info.get('source') or '')=='Unknown':
            score-=8; components.append({'label':'Unknown source','score':-8}); reasons.append('Source could not be identified')
        if episode is not None and current_quality and current_quality!='Unknown' and rank<999:
            cur=self._quality_rank(current_quality,profile)
            if cur<999:
                if rank<cur:
                    delta=min(18,max(4,(cur-rank)*4)); score+=delta; components.append({'label':f'Upgrade over {current_quality}','score':delta}); reasons.append(f'Improves current quality {current_quality}')
                else: rejects.append(f"Not an upgrade over current quality {current_quality}")
        accepted=not rejects; decision='ELIGIBLE' if accepted else 'REJECTED'
        return {'score':int(score),'parsed':info,'reasons':reasons,'score_components':components,'rejections':rejects,'accepted':accepted,'decision':decision}

    def _score_release(self,title:str,size:int,profile:dict[str,Any]):
        ev=self._evaluate_release(title,size,profile)
        return ev['score'],ev['parsed'],list(ev['reasons'])+list(ev['rejections']),ev['accepted']

    def _merge_scan_state(self, current:dict[str,Any], scanned:dict[str,Any]):
        """Merge only filesystem-derived scan fields into the live library record.

        User-editable monitoring/profile/root choices may change while a long scan is
        running, so never replace the whole item snapshot after scanning.
        """
        for key in ('library_root_status','last_scan_at'):
            if key in scanned: current[key]=copy.deepcopy(scanned.get(key))
        if 'library_scan_error' in scanned: current['library_scan_error']=str(scanned.get('library_scan_error') or '')
        else: current.pop('library_scan_error',None)
        if str(current.get('kind') or '')!='tv':
            current['movie_file']=copy.deepcopy(scanned.get('movie_file'))
            return
        scan_seasons={int(x.get('season_number') or 0):x for x in scanned.get('seasons') or [] if int(x.get('season_number') or 0)>0}
        file_keys=('has_file','file_path','file_quality','file_size','file_fingerprint','quality_source','media_info','cutoff_met')
        for season in current.get('seasons') or []:
            sn=int(season.get('season_number') or 0); src_season=scan_seasons.get(sn)
            if not src_season: continue
            src_eps={int(x.get('episode_number') or 0):x for x in src_season.get('episodes') or [] if int(x.get('episode_number') or 0)>0}
            for ep in season.get('episodes') or []:
                src=src_eps.get(int(ep.get('episode_number') or 0))
                if not src: continue
                for key in file_keys:
                    ep[key]=copy.deepcopy(src.get(key))

    def scan_library(self, ident=''):
        """Reconcile Automation against configured library folders without UI lock stalls.

        Filesystem traversal and media probing can take tens of seconds on large
        libraries. Work from a snapshot outside the global Automation mutation lock,
        then merge only filesystem-derived state back under a short commit lock.
        """
        with self.lock:
            lib=copy.deepcopy(self._library())
            profiles_list=copy.deepcopy(self._profiles())
        targets=[x for x in lib if not ident or str(x.get('id'))==str(ident)]
        profiles={str(p.get('id')):p for p in profiles_list}; files_by_root={}; scanned_paths=set()
        qcache=self._media_quality_cache(); qcache_changed=False; matched=0; changes=[]; offline=[]

        def files_for(root:Path|None):
            if not root: return None
            try: key=str(root.resolve()).casefold()
            except OSError: key=str(root).casefold()
            if key in files_by_root: return files_by_root[key]
            if not root.exists() or not root.is_dir():
                files_by_root[key]=None; return None
            rows=[]
            try: rows=[f for f in root.rglob('*') if f.is_file() and f.suffix.casefold() in VIDEO_EXTS]
            except OSError: return None
            files_by_root[key]=rows; scanned_paths.update(str(f) for f in rows); return rows

        for item in targets:
            profile=profiles.get(str(item.get('quality_profile_id'))) or (profiles_list[0] if profiles_list else DEFAULT_PROFILES[0])
            root=self._resolve_root(item); item_files=files_for(root)
            if item_files is None:
                prior=str(item.get('library_root_status') or '')
                item['library_root_status']='offline'; item['library_scan_error']='Configured Root Folder is unavailable'; item['last_scan_at']=_now()
                offline.append({'item_id':str(item.get('id') or ''),'title':str(item.get('title') or ''),'root':str(root or '')})
                if prior!='offline':
                    changes.append({'type':'root_offline','item_id':str(item.get('id') or ''),'title':str(item.get('title') or ''),'root':str(root or '')})
                continue
            if str(item.get('library_root_status') or '')=='offline':
                changes.append({'type':'root_online','item_id':str(item.get('id') or ''),'title':str(item.get('title') or ''),'root':str(root or '')})
            item['library_root_status']='online'; item.pop('library_scan_error',None)
            if item.get('kind')=='tv':
                previous={}
                for sr in item.get('seasons') or []:
                    for ep in sr.get('episodes') or []:
                        key=(int(sr.get('season_number',0) or 0),int(ep.get('episode_number',0) or 0)); previous[key]=dict(ep)
                        ep.update({'has_file':False,'file_path':'','file_quality':'','file_size':0,'file_fingerprint':'','quality_source':'','media_info':{},'cutoff_met':False})
                candidates={}
                for f in item_files:
                    if not _slug_match(str(f.parent.parent)+' '+f.name,item.get('title',''),item.get('year')): continue
                    m=re.search(r'\bS(\d{1,2})E(\d{1,3})\b',f.name,re.I)
                    if not m: continue
                    key=(int(m.group(1)),int(m.group(2)))
                    sr=next((x for x in item.get('seasons',[]) if int(x.get('season_number',0) or 0)==key[0]),None)
                    ep=next((x for x in (sr or {}).get('episodes',[]) if int(x.get('episode_number',0) or 0)==key[1]),None)
                    if not ep: continue
                    q,source,fp,changed=self._quality_for_media(f,qcache,previous.get(key)); qcache_changed|=changed
                    rec=(self._quality_rank(q,profile),-(f.stat().st_size if f.exists() else 0),f,q,source,fp)
                    if key not in candidates or rec[:2]<candidates[key][:2]: candidates[key]=rec
                for (sn,en),(_,neg_size,f,q,source,fp) in candidates.items():
                    sr=next((x for x in item.get('seasons',[]) if int(x.get('season_number',0) or 0)==sn),None)
                    ep=next((x for x in (sr or {}).get('episodes',[]) if int(x.get('episode_number',0) or 0)==en),None)
                    if ep is None: continue
                    ep.update({'has_file':True,'file_path':str(f),'file_quality':q,'file_size':-neg_size,'file_fingerprint':fp,'quality_source':source,'media_info':self._probe_media_traits(f),'cutoff_met':self._quality_cutoff_met(q,profile)}); matched+=1
                for key,old in previous.items():
                    sn,en=key; sr=next((x for x in item.get('seasons',[]) if int(x.get('season_number',0) or 0)==sn),None); ep=next((x for x in (sr or {}).get('episodes',[]) if int(x.get('episode_number',0) or 0)==en),None)
                    if ep is None: continue
                    if bool(old.get('has_file')) and not bool(ep.get('has_file')):
                        changes.append({'type':'file_missing','item_id':str(item.get('id') or ''),'title':str(item.get('title') or ''),'season':sn,'episode':en,'path':str(old.get('file_path') or '')})
                    elif not bool(old.get('has_file')) and bool(ep.get('has_file')):
                        changes.append({'type':'file_found','item_id':str(item.get('id') or ''),'title':str(item.get('title') or ''),'season':sn,'episode':en,'path':str(ep.get('file_path') or ''),'quality':str(ep.get('file_quality') or '')})
                    elif bool(ep.get('has_file')) and str(old.get('file_quality') or '') and str(old.get('file_quality') or '')!=str(ep.get('file_quality') or ''):
                        changes.append({'type':'quality_changed','item_id':str(item.get('id') or ''),'title':str(item.get('title') or ''),'season':sn,'episode':en,'from_quality':str(old.get('file_quality') or ''),'to_quality':str(ep.get('file_quality') or '')})
            else:
                previous=dict(item.get('movie_file') or {})
                candidates=[]
                for f in item_files:
                    if not _slug_match(str(f.parent)+' '+f.name,item.get('title',''),item.get('year')): continue
                    q,source,fp,changed=self._quality_for_media(f,qcache,previous); qcache_changed|=changed
                    candidates.append((self._quality_rank(q,profile),-(f.stat().st_size if f.exists() else 0),f,q,source,fp))
                item['movie_file']=None
                if candidates:
                    _,neg_size,f,q,source,fp=min(candidates,key=lambda x:x[:2])
                    item['movie_file']={'path':str(f),'quality':q,'size':-neg_size,'file_fingerprint':fp,'quality_source':source,'media_info':self._probe_media_traits(f),'cutoff_met':self._quality_cutoff_met(q,profile)}; matched+=1
                current=item.get('movie_file') or {}
                if previous and not current:
                    changes.append({'type':'file_missing','item_id':str(item.get('id') or ''),'title':str(item.get('title') or ''),'path':str(previous.get('path') or '')})
                elif not previous and current:
                    changes.append({'type':'file_found','item_id':str(item.get('id') or ''),'title':str(item.get('title') or ''),'path':str(current.get('path') or ''),'quality':str(current.get('quality') or '')})
                elif previous and current and str(previous.get('quality') or '')!=str(current.get('quality') or ''):
                    changes.append({'type':'quality_changed','item_id':str(item.get('id') or ''),'title':str(item.get('title') or ''),'from_quality':str(previous.get('quality') or ''),'to_quality':str(current.get('quality') or '')})
            item['last_scan_at']=_now()

        scanned={str(x.get('id') or ''):x for x in targets if str(x.get('id') or '')}
        with self.lock:
            fresh=self._library()
            for current in fresh:
                source=scanned.get(str(current.get('id') or ''))
                if source: self._merge_scan_state(current,source)
            self._save_library(fresh)
        if qcache_changed: _write(self.media_quality_cache_file,qcache)
        for change in changes[:80]:
            typ=change.get('type'); label=change.get('title') or 'Media'
            if change.get('season') is not None: label+=f" {_episode_token(change.get('season'),change.get('episode'))}"
            messages={'root_offline':f'Root Folder offline for {label}','root_online':f'Root Folder restored for {label}','file_missing':f'Library file is missing for {label}','file_found':f'Library file found for {label}','quality_changed':f'Library quality changed for {label}'}
            self._event(str(typ),messages.get(str(typ),f'Library changed for {label}'),**change)
        self._event('scan',f'Library scan matched {matched} media file(s)',matched=matched,files=len(scanned_paths),changes=len(changes),offline_roots=len(offline))
        return {'ok':True,'matched':matched,'files_scanned':len(scanned_paths),'items_scanned':len(targets),'changes':changes,'offline_roots':offline,'library':fresh}

    def _resolve_root(self, item: dict[str,Any], required_bytes:int=0) -> Path | None:
        configured=str(item.get('root_folder') or '').strip()
        if configured:
            return Path(configured).expanduser()
        cfg=self._config(); roots=[Path(str(x).strip()).expanduser() for x in (cfg.get('tv_roots' if item.get('kind')=='tv' else 'movie_roots') or []) if str(x).strip()]
        if not roots: return None


        existing=self._existing_media_path(item)
        if existing:
            for root in roots:
                try:
                    existing.resolve().relative_to(root.resolve()); return root
                except (OSError,ValueError): pass
        online=[r for r in roots if r.exists() and r.is_dir()]
        if not online: return roots[0]
        if required_bytes>0:
            eligible=[r for r in online if self._disk_free(r)>=int(required_bytes)]
            if eligible: return max(eligible,key=self._disk_free)
        return online[0]

    def _template(self, template: str, values: dict[str,Any], fallback: str) -> str:
        class Safe(dict):
            def __missing__(self,key): return ''
        try:
            rendered=template.format_map(Safe(values))
        except Exception:
            rendered=fallback
        return _safe_component(rendered, fallback)

    def _tv_episode_from_filename(self, path:Path, *, expected_season:int|None=None) -> tuple[int|None,int|None,str]:
        """Conservatively identify one TV episode from a completed media filename."""
        name=path.name
        m=re.search(r'\bS(\d{1,2})E(\d{1,3})(?!E\d)',name,re.I)
        if m: return int(m.group(1)),int(m.group(2)),'SxxEyy filename'
        m=re.search(r'\b(\d{1,2})x(\d{1,3})\b',name,re.I)
        if m: return int(m.group(1)),int(m.group(2)),'NxNN filename'
        if expected_season is not None:
            m=re.search(r'(?i)(?:^|[ ._\-])E(\d{1,3})(?:[ ._\-]|$)',name)
            if m: return int(expected_season),int(m.group(1)),'Exx filename + pack season context'
        return None,None,'No unambiguous episode token'

    def _build_import_plan(self, item:dict[str,Any], context:dict[str,Any], files:list[Path], root:Path, profile:dict[str,Any]) -> dict[str,Any]:
        """Classify completed media and return an explainable, non-destructive plan."""
        title=str(item.get('title') or context.get('title') or 'Media'); year=item.get('year') or context.get('year') or ''
        release_title=str(context.get('release_title') or ''); release_quality=str(context.get('release_quality') or parse_release(release_title).get('quality') or 'Unknown')
        cfg=self._config(); inspections=[]; entries=[]
        candidates=[]
        for f in files:
            marker=re.search(r'(?i)(?:^|[ ._\-])(sample|proof|trailer|extras?)(?:[ ._\-]|$)',f.name)
            if marker:
                inspections.append({'source':str(f),'identified':'Non-feature media','quality':'','action':'IGNORE','destination':'','reason':f'{marker.group(1)} marker'})
                continue
            candidates.append(f)
        if item.get('kind')=='movie':
            matched=[f for f in candidates if _slug_match(str(f.parent)+' '+f.name,title,year)]
            pool=matched or candidates
            if not pool: return {'entries':[],'inspections':inspections,'error':'No completed feature video file was found to import'}
            source=max(pool,key=lambda p:p.stat().st_size if p.exists() else 0)
            q=parse_release(source.name).get('quality') or 'Unknown'; quality=q if q!='Unknown' else release_quality
            values={'title':title,'year':year or '','quality':quality,'release_group':str(context.get('release_group') or ''),'episode_title':''}
            folder=self._template(str(cfg.get('movie_folder_template') or '{title} ({year})'),values,_safe_component(f'{title} ({year})' if year else title))
            base=self._template(str(cfg.get('movie_file_template') or '{title} ({year})'),values,_safe_component(f'{title} ({year})' if year else title))
            if bool(cfg.get('plex_include_quality',False)) and quality and quality!='Unknown': base=_safe_component(f'{base} [{quality}]',base)
            dest=root/folder/(base+source.suffix.casefold()); old=dict(item.get('movie_file') or {}); old_quality=str(old.get('quality') or '')
            existing=Path(str(old.get('path') or dest)) if (old.get('path') or dest.exists()) else None
            action='IMPORT'; reason='No existing movie file'
            if existing is not None and existing.exists():
                sfp=self._media_fingerprint(source); efp=self._media_fingerprint(existing)
                if sfp and efp and sfp==efp: action='DUPLICATE'; reason='Existing library file has the same fingerprint'
                elif old_quality and old_quality!='Unknown' and self._quality_rank(quality,profile)>=self._quality_rank(old_quality,profile): action='KEEP_EXISTING'; reason=f'Existing {old_quality} is equal or better than {quality}'
                else: action='UPGRADE'; reason=f'{old_quality or "Existing file"} → {quality}'
            entries.append({'source':source,'dest':dest,'quality':quality,'action':action,'reason':reason,'old_quality':old_quality,'existing_path':str(existing) if existing is not None and existing.exists() else '', 'episode':None,'season':None,'episode_title':''})
            inspections.append({'source':str(source),'identified':f'{title} ({year})' if year else title,'quality':quality,'action':action,'destination':str(dest),'reason':reason})
            for f in candidates:
                if f!=source: inspections.append({'source':str(f),'identified':'Additional video','quality':str(parse_release(f.name).get('quality') or ''),'action':'IGNORE','destination':'','reason':'Movie import selected the strongest main feature candidate'})
        else:
            season_ctx=int(context.get('season') or 0) if context.get('season') is not None else None
            target_ep=int(context.get('episode') or 0) if context.get('episode') is not None else None
            season_pack=bool(context.get('season_pack'))

            # NZBGeek and other indexers deliberately obfuscate payload filenames.
            # For an exact single-episode Automation target, release identity comes
            # from the preserved grab context, not from the payload filename. If no
            # video file exposes any episode token, safely nominate the only/dominant
            # feature video as the requested episode. This still refuses ambiguous
            # sets containing multiple similarly-sized opaque feature files.
            opaque_context_source=None
            if not season_pack and target_ep is not None and season_ctx is not None and candidates:
                identified=[]; unknown=[]
                for candidate in candidates:
                    cs,ce,_=self._tv_episode_from_filename(candidate,expected_season=None)
                    if cs is None or ce is None: unknown.append(candidate)
                    else: identified.append((candidate,cs,ce))
                has_exact=any(cs==season_ctx and ce==target_ep for _,cs,ce in identified)
                if not has_exact and not identified and unknown:
                    ranked=sorted(unknown,key=lambda x:(x.stat().st_size if x.exists() else 0),reverse=True)
                    if len(ranked)==1:
                        opaque_context_source=ranked[0]
                    elif ranked:
                        largest=max(0,int(ranked[0].stat().st_size if ranked[0].exists() else 0))
                        second=max(0,int(ranked[1].stat().st_size if ranked[1].exists() else 0))
                        if largest >= 256*1024*1024 and (second < 200*1024*1024 or largest >= max(1,second)*2.5):
                            opaque_context_source=ranked[0]
            seen={}
            for source in candidates:
                parsed=parse_release(source.name)
                if parsed.get('is_multi_episode'):
                    inspections.append({'source':str(source),'identified':'Multi-episode file','quality':str(parsed.get('quality') or ''),'action':'NEEDS_ATTENTION','destination':'','reason':'One file maps to multiple episode numbers; automatic splitting/duplication is unsafe'})
                    continue
                sn,en,why=self._tv_episode_from_filename(source,expected_season=season_ctx if season_pack else None)
                if not season_pack and target_ep:
                    if sn is None or en is None:
                        if source==opaque_context_source:
                            sn,en=season_ctx,target_ep; why='Obfuscated filename mapped from exact Automation target context'
                        elif len(candidates)==1:
                            sn,en=season_ctx,target_ep; why='Single-file target context fallback'
                    if sn!=season_ctx or en!=target_ep:
                        inspections.append({'source':str(source),'identified':'Different/unknown episode','quality':str(parsed.get('quality') or ''),'action':'IGNORE','destination':'','reason':f'Expected S{int(season_ctx or 0):02d}E{int(target_ep):02d}; {why}'})
                        continue
                if sn is None or en is None:
                    inspections.append({'source':str(source),'identified':'Unknown episode','quality':str(parsed.get('quality') or ''),'action':'NEEDS_ATTENTION','destination':'','reason':why})
                    continue
                if season_ctx and sn!=season_ctx:
                    inspections.append({'source':str(source),'identified':f'S{sn:02d}E{en:02d}','quality':str(parsed.get('quality') or ''),'action':'IGNORE','destination':'','reason':f'Outside requested Season {season_ctx}'})
                    continue
                sr=next((x for x in item.get('seasons',[]) if int(x.get('season_number',0) or 0)==sn),None)
                ep=next((x for x in (sr or {}).get('episodes',[]) if int(x.get('episode_number',0) or 0)==en),None)
                if ep is None:
                    inspections.append({'source':str(source),'identified':f'S{sn:02d}E{en:02d}','quality':str(parsed.get('quality') or ''),'action':'IGNORE','destination':'','reason':'Episode is not present in Automation metadata'})
                    continue
                exact_target=bool(not season_pack and target_ep is not None and season_ctx is not None and sn==season_ctx and en==target_ep)
                if ep.get('monitored') is False and not exact_target:
                    inspections.append({'source':str(source),'identified':f'S{sn:02d}E{en:02d}','quality':str(parsed.get('quality') or ''),'action':'IGNORE','destination':'','reason':'Episode is unmonitored'})
                    continue
                q=str(parsed.get('quality') or 'Unknown'); quality=q if q!='Unknown' else release_quality
                ep_title=str(ep.get('name') or f'Episode {en}'); token=_episode_token(sn,en)
                library_title=self._tv_library_title(item,release_title=release_title)
                values={'title':title,'library_title':library_title,'year':year or '','quality':quality,'release_group':str(context.get('release_group') or ''),'episode_title':ep_title,'season':sn,'episode':en,'episode_token':token}
                show_dir=self._tv_series_folder(item,root,cfg,values)
                season_folder=self._template(str(cfg.get('tv_season_template') or 'Season {season}'),values,f'Season {sn}')
                base=self._template(str(cfg.get('tv_file_template') or '{library_title} - {episode_token} - {episode_title}'),values,f'{library_title} - {token} - {ep_title}')
                if bool(cfg.get('plex_include_quality',False)) and quality and quality!='Unknown': base=_safe_component(f'{base} [{quality}]',base)
                dest=show_dir/season_folder/(base+source.suffix.casefold()); old_quality=str(ep.get('file_quality') or '')
                existing=Path(str(ep.get('file_path') or dest)) if (ep.get('file_path') or dest.exists()) else dest
                action='IMPORT'; reason='Explicitly targeted episode download' if exact_target and ep.get('monitored') is False else 'Episode is missing'
                if existing.exists() or ep.get('has_file'):
                    if existing.exists():
                        sfp=self._media_fingerprint(source); efp=self._media_fingerprint(existing)
                        if sfp and efp and sfp==efp: action='DUPLICATE'; reason='Existing episode has the same fingerprint'
                        elif old_quality and old_quality!='Unknown' and self._quality_rank(quality,profile)>=self._quality_rank(old_quality,profile): action='KEEP_EXISTING'; reason=f'Existing {old_quality} is equal or better than {quality}'
                        else: action='UPGRADE'; reason=f'{old_quality or "Existing file"} → {quality}'
                key=(sn,en)
                prev=seen.get(key)
                candidate={'source':source,'dest':dest,'quality':quality,'action':action,'reason':reason,'old_quality':old_quality,'existing_path':str(existing) if existing.exists() else '', 'episode':en,'season':sn,'episode_title':ep_title,'episode_ref':ep}
                if prev is None or (self._quality_rank(quality,profile),-(source.stat().st_size if source.exists() else 0)) < (self._quality_rank(prev['quality'],profile),-(prev['source'].stat().st_size if prev['source'].exists() else 0)):
                    if prev is not None: inspections.append({'source':str(prev['source']),'identified':f'S{sn:02d}E{en:02d}','quality':prev['quality'],'action':'IGNORE','destination':'','reason':'A stronger candidate for the same episode was present'})
                    seen[key]=candidate
                else:
                    inspections.append({'source':str(source),'identified':f'S{sn:02d}E{en:02d}','quality':quality,'action':'IGNORE','destination':'','reason':'A stronger candidate for the same episode was present'})
            entries.extend(seen.values())
            for e in entries:
                inspections.append({'source':str(e['source']),'identified':f"{title} S{int(e['season']):02d}E{int(e['episode']):02d} — {e['episode_title']}",'quality':e['quality'],'action':e['action'],'destination':str(e['dest']),'reason':e['reason']})
        return {'entries':entries,'inspections':inspections,'error':''}

    def _commit_import_plan(self, entries:list[dict[str,Any]], root:Path, progress_callback:Callable[[float,str],None]|None=None) -> list[dict[str,Any]]:
        """Stage + verify every actionable file, then commit with rollback backups."""
        actionable=[e for e in entries if e.get('action') in {'IMPORT','UPGRADE'}]
        reserve=max(1,int(self.public_config().get('automatic_storage_reserve_gb') or 5))*1024**3
        copy_required=0
        try: root_dev=root.stat().st_dev
        except OSError: root_dev=None
        for e in actionable:
            try:
                src=Path(e['source'])
                if root_dev is None or src.stat().st_dev!=root_dev:
                    copy_required += int(src.stat().st_size)
            except OSError:
                pass
        required=copy_required + reserve
        if actionable and self._disk_free(root)<required:
            raise OSError(f'Not enough free space in Root Folder {root}. Need about {required/1024**3:.1f} GB including safety reserve.')
        staged=[]; committed=[]
        total_copy_bytes=sum(max(0,int(e['source'].stat().st_size)) for e in actionable if e.get('source') and e['source'].exists())
        copied_bytes=0
        last_emit=0.0
        def emit(percent:float,message:str):
            nonlocal last_emit
            if not progress_callback: return
            now=time.monotonic()
            if percent < 100 and now-last_emit < 0.35: return
            last_emit=now
            try: progress_callback(percent,message)
            except Exception: pass
        try:
            emit(2,'Smart Import • preparing media transaction')
            for i,e in enumerate(actionable):
                src=Path(e['source']); dest=Path(e['dest']); dest.parent.mkdir(parents=True,exist_ok=True)
                temp=dest.with_name(dest.name+f'.newzdeck-{os.getpid()}-{i}.tmp')
                src_size=max(0,int(src.stat().st_size))
                moved_source=False
                try:
                    same_fs = src.stat().st_dev == dest.parent.stat().st_dev
                except OSError:
                    same_fs = False
                if same_fs:
                    emit(10 + (80 * copied_bytes / max(1,total_copy_bytes)), f'Smart Import • staging {src.name}')
                    os.replace(src,temp)
                    moved_source=True
                    copied_bytes += src_size
                else:
                    with src.open('rb') as inp,temp.open('wb') as out:
                        while True:
                            chunk=inp.read(8*1024*1024)
                            if not chunk: break
                            out.write(chunk); copied_bytes += len(chunk)
                            pct=10 + (80 * copied_bytes / max(1,total_copy_bytes))
                            emit(pct,f'Smart Import • copying {src.name} • {copied_bytes/1024**3:.1f} / {total_copy_bytes/1024**3:.1f} GB')
                        out.flush(); os.fsync(out.fileno())
                if temp.stat().st_size!=src_size: raise IOError(f'Imported media size verification failed for {src.name}')
                sfp=(self._media_fingerprint(temp) if moved_source else self._media_fingerprint(src)); tfp=self._media_fingerprint(temp)
                if sfp and tfp and sfp!=tfp: raise IOError(f'Imported media fingerprint verification failed for {src.name}')
                e['_temp']=temp; e['_source_moved']=moved_source; e['_expected_size']=src_size; e['_expected_fp']=tfp; staged.append(e)
            emit(92,'Smart Import • committing verified media')
            for i,e in enumerate(staged):
                dest=Path(e['dest']); temp=Path(e['_temp']); backup=None; old_backup=None
                existing=Path(str(e.get('existing_path') or '')) if str(e.get('existing_path') or '') else None
                same_existing=False
                if existing is not None:
                    try: same_existing=existing.resolve()==dest.resolve()
                    except OSError: same_existing=str(existing).casefold()==str(dest).casefold()
                if dest.exists():
                    backup=dest.with_name(dest.name+f'.newzdeck-backup-{os.getpid()}-{i}')
                    os.replace(dest,backup)
                if e.get('action')=='UPGRADE' and existing is not None and existing.exists() and not same_existing:
                    old_backup=existing.with_name(existing.name+f'.newzdeck-backup-{os.getpid()}-{i}')
                    os.replace(existing,old_backup)
                try:
                    os.replace(temp,dest); e['_backup']=backup; e['_old_backup']=old_backup; e['_old_path']=existing; committed.append(e)
                except Exception:
                    if backup and backup.exists(): os.replace(backup,dest)
                    if old_backup and old_backup.exists() and existing is not None: os.replace(old_backup,existing)
                    raise
            # Verify the final library paths themselves before deleting either the
            # source copy or rollback backups. This makes cross-volume copy -> verify
            # -> commit semantics explicit and leaves the staging package recoverable
            # if storage returns a short write or the destination changes underneath us.
            for e in committed:
                dest=Path(e['dest']); expected_size=max(0,int(e.get('_expected_size') or 0))
                if not dest.exists() or (expected_size and int(dest.stat().st_size)!=expected_size):
                    raise IOError(f'Final library verification failed for {dest.name}')
                expected_fp=str(e.get('_expected_fp') or '')
                final_fp=self._media_fingerprint(dest)
                if expected_fp and final_fp and expected_fp!=final_fp:
                    raise IOError(f'Final library fingerprint verification failed for {dest.name}')
            for e in committed:
                backup=e.get('_backup'); old_backup=e.get('_old_backup')
                if isinstance(backup,Path): backup.unlink(missing_ok=True)
                if isinstance(old_backup,Path): old_backup.unlink(missing_ok=True)
            for e in actionable:
                if e.get('_source_moved'):
                    continue
                try: Path(e['source']).unlink(missing_ok=True)
                except OSError: pass
            emit(100,'Smart Import • media committed')
            return actionable
        except Exception:
            for e in reversed(committed):
                dest=Path(e['dest']); backup=e.get('_backup'); old_backup=e.get('_old_backup'); old_path=e.get('_old_path'); src=Path(e['source'])
                try:
                    if e.get('_source_moved') and dest.exists() and not src.exists():
                        src.parent.mkdir(parents=True,exist_ok=True); os.replace(dest,src)
                    else:
                        dest.unlink(missing_ok=True)
                    if isinstance(backup,Path) and backup.exists(): os.replace(backup,dest)
                    if isinstance(old_backup,Path) and old_backup.exists() and isinstance(old_path,Path): os.replace(old_backup,old_path)
                except OSError: pass
            for e in staged:
                if e in committed: continue
                try:
                    t=e.get('_temp'); src=Path(e['source'])
                    if e.get('_source_moved') and isinstance(t,Path) and t.exists() and not src.exists():
                        src.parent.mkdir(parents=True,exist_ok=True); os.replace(t,src)
                    elif isinstance(t,Path):
                        t.unlink(missing_ok=True)
                except OSError: pass
            raise

    def _one_time_import_item(self, context:dict[str,Any], root:Path, profile:dict[str,Any]) -> dict[str,Any]:
        """Build a non-persistent media item for a one-time Discover grab.

        The item intentionally resembles an Automation library row closely enough to
        reuse Smart Import naming/quality logic, but it is never added to the library.
        """
        kind='tv' if str(context.get('kind') or '').lower()=='tv' else 'movie'
        title=str(context.get('title') or '').strip() or ('TV Show' if kind=='tv' else 'Movie')
        year=int(context.get('year')) if str(context.get('year') or '').isdigit() else None
        item={'id':'','kind':kind,'title':title,'year':year,
              'quality_profile_id':str(context.get('quality_profile_id') or profile.get('id') or ''),
              'root_folder':str(root),'movie_file':None,'seasons':[],'monitored':False,'monitor_mode':'none'}
        if kind=='tv':
            season=int(context.get('season') or 0) if context.get('season') is not None else 0
            episode=int(context.get('episode') or 0) if context.get('episode') is not None else 0
            known=[]
            for raw in context.get('manual_episodes') or []:
                if not isinstance(raw,dict): continue
                try: sn=int(raw.get('season') if raw.get('season') is not None else season); en=int(raw.get('episode'))
                except (TypeError,ValueError): continue
                if sn<=0 or en<=0: continue
                known.append((sn,en,str(raw.get('name') or f'Episode {en}')))
            if episode>0 and not any(sn==season and en==episode for sn,en,_ in known):
                known.append((season,episode,str(context.get('episode_title') or f'Episode {episode}')))
            by_season={}
            for sn,en,name in known:
                by_season.setdefault(sn,[]).append({'episode_number':en,'name':name,'monitored':True,'has_file':False,'file_path':'','file_quality':'','file_size':0,'cutoff_met':False})
            item['seasons']=[{'season_number':sn,'monitored':True,'episodes':sorted(rows,key=lambda x:int(x.get('episode_number') or 0))} for sn,rows in sorted(by_season.items())]
        return item

    def _hydrate_one_time_existing_media(self, item:dict[str,Any], context:dict[str,Any], root:Path, profile:dict[str,Any]) -> None:
        """Populate existing-media state without creating an Automation library row."""
        try:
            candidates=[]
            for f in root.rglob('*'):
                if not f.is_file() or f.suffix.casefold() not in VIDEO_EXTS: continue
                if not _slug_match(str(f.parent)+' '+f.name,str(item.get('title') or ''),item.get('year')): continue
                candidates.append(f)
                if len(candidates)>=5000: break
        except OSError:
            return
        if item.get('kind')=='movie':
            ranked=[]
            for f in candidates:
                q=str(parse_release(f.name).get('quality') or 'Unknown')
                try: size=int(f.stat().st_size)
                except OSError: size=0
                ranked.append((self._quality_rank(q,profile),-size,f,q))
            if ranked:
                _,neg_size,f,q=min(ranked,key=lambda x:x[:2])
                item['movie_file']={'path':str(f),'quality':q,'size':-neg_size,'file_fingerprint':self._media_fingerprint(f),'quality_source':'existing-library','media_info':self._probe_media_traits(f),'cutoff_met':self._quality_cutoff_met(q,profile)}
            return
        refs={}
        for sr in item.get('seasons') or []:
            sn=int(sr.get('season_number') or 0)
            for ep in sr.get('episodes') or []: refs[(sn,int(ep.get('episode_number') or 0))]=ep
        for f in candidates:
            sn,en,_=self._tv_episode_from_filename(f,expected_season=None)
            ep=refs.get((int(sn or 0),int(en or 0)))
            if ep is None: continue
            q=str(parse_release(f.name).get('quality') or 'Unknown')
            try: size=int(f.stat().st_size)
            except OSError: size=0
            current=str(ep.get('file_quality') or '')
            if ep.get('has_file') and current and self._quality_rank(current,profile)<=self._quality_rank(q,profile): continue
            ep.update({'has_file':True,'file_path':str(f),'file_quality':q,'file_size':size,'file_fingerprint':self._media_fingerprint(f),'quality_source':'existing-library','media_info':self._probe_media_traits(f),'cutoff_met':self._quality_cutoff_met(q,profile)})

    def import_completed_download(self, context: dict[str,Any], candidates: list[str|Path], *, staging_dir: str|Path|None=None, progress_callback:Callable[[float,str],None]|None=None) -> dict[str,Any]:
        """Inspect, transactionally import, and reconcile a completed media grab.

        Automation grabs update the monitored library. Discover one-time media grabs
        reuse the same verified rename/move transaction without creating Automation
        monitoring state.
        """
        if not _is_smart_import_context(context): return {'ok':False,'skipped':True,'reason':'Not a Smart Import media grab'}
        cfg=self._config()
        if not bool(cfg.get('plex_organize_enabled',True)): return {'ok':False,'skipped':True,'reason':'Smart Import organization is disabled'}
        one_time=str(context.get('source') or '')=='manual_media_grab'
        with self.lock:
            lib=self._library()
            item=next((x for x in lib if str(x.get('id'))==str(context.get('item_id') or '')),None) if not one_time else None
            planned=str(context.get('planned_root_folder') or '').strip()
            if one_time:
                profiles=self._profiles(); profile=next((p for p in profiles if str(p.get('id'))==str(context.get('quality_profile_id') or '')),profiles[0])
                provisional={'kind':str(context.get('kind') or 'movie'),'title':str(context.get('title') or ''),'year':context.get('year'),'root_folder':planned}
                root=Path(planned).expanduser() if planned else self._resolve_root(provisional)
                if not root: return {'ok':False,'needs_root':True,'reason':f"Add a {'TV' if provisional.get('kind')=='tv' else 'Movie'} root folder in Automation Setup before using one-time media import"}
                item=self._one_time_import_item(context,root,profile)
                self._hydrate_one_time_existing_media(item,context,root,profile)
            else:
                if not item: return {'ok':False,'skipped':True,'reason':'Automation library item no longer exists'}
                root=Path(planned).expanduser() if planned else self._resolve_root(item)
                profile=next((p for p in self._profiles() if str(p.get('id'))==str(item.get('quality_profile_id'))),self._profiles()[0])
            if not root: return {'ok':False,'needs_root':True,'reason':f"Add a {'TV' if item.get('kind')=='tv' else 'Movie'} root folder in Automation Setup"}
            if not root.exists() or not root.is_dir(): return {'ok':False,'needs_root':True,'reason':f'Configured Root Folder is unavailable: {root}'}
            files=[]
            for raw in candidates or []:
                q=Path(raw)
                if q.is_dir():
                    try: files.extend(x for x in q.rglob('*') if x.is_file() and x.suffix.casefold() in VIDEO_EXTS)
                    except OSError: pass
                elif q.is_file() and q.suffix.casefold() in VIDEO_EXTS: files.append(q)
            unique=[]; seen=set()
            for f in files:
                try: k=str(f.resolve()).casefold()
                except OSError: k=str(f).casefold()
                if k not in seen: unique.append(f); seen.add(k)
            files=unique
            if not files:
                return {
                    'ok':False,'skipped':False,'retryable':True,
                    'reason':'Completed download is still settling in the SAB output folder; Smart Import will retry automatically.'
                }
            plan=self._build_import_plan(item,context,files,root,profile)
            if plan.get('error'): return {'ok':False,'needs_attention':True,'reason':str(plan.get('error')),'inspection':plan.get('inspections') or []}
            entries=list(plan.get('entries') or []); inspections=list(plan.get('inspections') or [])
            attention=[x for x in inspections if x.get('action')=='NEEDS_ATTENTION']
            if not entries:
                self._event('import-inspection',f"Import Inspector found no safe target for {item.get('title')}",item_id=item.get('id'),season=context.get('season'),episode=context.get('episode'),season_pack=bool(context.get('season_pack')),inspections=inspections[:80],needs_attention=max(1,len(attention)),imported=0)
                return {'ok':False,'needs_attention':True,'reason':'No completed media matched the requested media target. The downloaded/extracted files were preserved for review.','inspection':inspections}
            if attention and not any(e.get('action') in {'IMPORT','UPGRADE','DUPLICATE','KEEP_EXISTING'} for e in entries):
                self._event('import-inspection',f"Import Inspector needs attention for {item.get('title')}",item_id=item.get('id'),season=context.get('season'),season_pack=bool(context.get('season_pack')),inspections=inspections[:80],needs_attention=len(attention),imported=0)
                return {'ok':False,'needs_attention':True,'reason':'Import Inspector could not safely identify the completed media. Review the filenames before retrying.','inspection':inspections}

            if progress_callback:
                try: progress_callback(0,'Smart Import • inspecting completed media')
                except Exception: pass
            committed=self._commit_import_plan(entries,root,progress_callback=progress_callback)

            # A duplicate/equal-or-better library match is a successful Automation
            # outcome, not a reason to leave a second downloaded media copy in the
            # staging folder. Only remove files proven redundant and only when they
            # are inside this SAB job's own staging directory.
            if staging_dir and bool(cfg.get('plex_cleanup_staging',True)):
                try:
                    stage_root=Path(staging_dir).resolve()
                    for e in entries:
                        if str(e.get('action') or '') not in {'DUPLICATE','KEEP_EXISTING'}:
                            continue
                        src=Path(e['source'])
                        try:
                            resolved=src.resolve()
                            resolved.relative_to(stage_root)
                        except (OSError,ValueError):
                            continue
                        try: resolved.unlink(missing_ok=True)
                        except OSError: pass
                except OSError:
                    pass

            imported=[]; kept_existing_files=[]
            for e in entries:
                action=str(e.get('action') or '')
                if action not in {'IMPORT','UPGRADE','DUPLICATE','KEEP_EXISTING'}: continue
                dest=Path(e['dest']); quality=str(e.get('quality') or 'Unknown')
                if action in {'DUPLICATE','KEEP_EXISTING'}:
                    # v3.5.39: a duplicate/equal-or-better library match is a real
                    # successful Smart Import outcome. Reconcile the Automation
                    # library record immediately instead of waiting for the next
                    # periodic library scan. This is especially important for Movies:
                    # leaving movie_file unset made a completed duplicate look Missing
                    # again and could trigger another download of the same title.
                    existing_raw=str(e.get('existing_path') or '').strip()
                    existing=Path(existing_raw) if existing_raw else None
                    if existing is not None and existing.exists():
                        existing_quality=str(e.get('old_quality') or '')
                        if not existing_quality or existing_quality=='Unknown':
                            existing_quality=quality if action=='DUPLICATE' else (existing_quality or 'Unknown')
                        fp=self._media_fingerprint(existing)
                        cutoff=self._quality_cutoff_met(existing_quality,profile)
                        media_bytes=int(existing.stat().st_size)
                        record={'path':str(existing),'quality':existing_quality,'size':media_bytes,'file_fingerprint':fp,'quality_source':'existing-library','media_info':self._probe_media_traits(existing),'cutoff_met':cutoff}
                        if item.get('kind')=='tv':
                            ep=e.get('episode_ref')
                            if isinstance(ep,dict): ep.update({'has_file':True,'file_path':str(existing),'file_quality':existing_quality,'file_size':media_bytes,'file_fingerprint':fp,'quality_source':'existing-library','media_info':record['media_info'],'cutoff_met':cutoff})
                        else:
                            item['movie_file']=record
                        kept_existing_files.append({'destination':str(existing),'quality':existing_quality,'action':action,'season':e.get('season'),'episode':e.get('episode'),'from_quality':str(e.get('old_quality') or ''),'bytes':media_bytes,'source_filename':Path(e['source']).name,'final_filename':existing.name})
                        self._event('import-existing',f"Kept existing library file {existing.name}",item_id=item.get('id'),target_key=str(context.get('target_key') or ''),destination=str(existing),final_filename=existing.name,final_folder=str(existing.parent),file_size=media_bytes,source_filename=Path(e['source']).name,release_title=str(context.get('release_title') or ''),quality=existing_quality,season=e.get('season'),episode=e.get('episode'),season_pack=bool(context.get('season_pack')),verified=True,decision=action)
                    continue
                fp=self._remember_media_quality(dest,quality,str(context.get('release_title') or ''))
                cutoff=self._quality_cutoff_met(quality,profile)
                if item.get('kind')=='tv':
                    ep=e.get('episode_ref')
                    if isinstance(ep,dict): ep.update({'has_file':True,'file_path':str(dest),'file_quality':quality,'file_size':dest.stat().st_size,'file_fingerprint':fp,'quality_source':'newzdeck-import','media_info':self._probe_media_traits(dest),'cutoff_met':cutoff})
                else:
                    item['movie_file']={'path':str(dest),'quality':quality,'size':dest.stat().st_size,'file_fingerprint':fp,'quality_source':'newzdeck-import','media_info':self._probe_media_traits(dest),'cutoff_met':cutoff}
                media_bytes=int(dest.stat().st_size)
                imported.append({'destination':str(dest),'quality':quality,'action':action,'season':e.get('season'),'episode':e.get('episode'),'from_quality':str(e.get('old_quality') or ''),'bytes':media_bytes,'source_filename':Path(e['source']).name,'final_filename':dest.name})
                self._event('upgrade-import' if action=='UPGRADE' else 'import',f"{'Upgraded' if action=='UPGRADE' else 'Imported'} {dest.name}",item_id=item.get('id'),target_key=str(context.get('target_key') or ''),destination=str(dest),final_filename=dest.name,final_folder=str(dest.parent),file_size=media_bytes,source_filename=Path(e['source']).name,release_title=str(context.get('release_title') or ''),release_size=int(context.get('release_size') or 0),quality=quality,from_quality=str(e.get('old_quality') or ''),to_quality=quality,indexer=str(context.get('indexer') or ''),season=e.get('season'),episode=e.get('episode'),episode_title=str(e.get('episode_title') or ''),season_pack=bool(context.get('season_pack')),verified=True)
            item['last_scan_at']=_now(); item['updated_at']=_now(); item['library_root_status']='online'
            if not one_time:
                self._save_library(lib)
            self._event('import-inspection',f"Import Inspector processed {len(files)} video file(s) for {item.get('title')}",item_id=item.get('id'),source=str(context.get('source') or ''),season=context.get('season'),episode=context.get('episode'),season_pack=bool(context.get('season_pack')),inspections=inspections[:80],imported=len(imported),ignored=sum(1 for x in inspections if x.get('action')=='IGNORE'),needs_attention=len(attention))
            if not one_time:
                try:
                    rt=self._auto_runtime(); key=str(context.get('target_key') or self._auto_target_key(context=context)); targets=rt.get('targets') if isinstance(rt.get('targets'),dict) else {}; rt['targets']=targets; rec=targets.setdefault(key,{}) if key else {}
                    if key:
                        primary_row=(imported[0] if imported else (kept_existing_files[0] if kept_existing_files else {}))
                        message=f"Imported {len(imported)} episode(s) from season pack" if context.get('season_pack') else (f"Imported {Path(imported[0]['destination']).name}" if imported else (f"Import complete; existing library file kept • {Path(primary_row.get('destination') or '').name}" if primary_row.get('destination') else 'Import complete; existing library file kept'))
                        rec.update({'status':'imported','message':message,'updated_ts':time.time(),'imported_path':str(primary_row.get('destination') or ''),'imported_quality':str(primary_row.get('quality') or ''),'imported_count':len(imported),'kept_existing_count':len(kept_existing_files),'season_pack':bool(context.get('season_pack'))})
                        self._record_indexer_outcome(rt,str(context.get('indexer') or rec.get('last_indexer') or ''),success=True); self._save_auto_runtime(rt)
                except Exception: pass
        if bool(cfg.get('plex_cleanup_staging',True)) and staging_dir:
            try:
                sd=Path(staging_dir)
                for d in sorted([x for x in sd.rglob('*') if x.is_dir()],key=lambda x:len(x.parts),reverse=True):
                    try: d.rmdir()
                    except OSError: pass
                try: sd.rmdir()
                except OSError: pass
            except OSError: pass
        primary=str(imported[0]['destination']) if imported else (str(kept_existing_files[0]['destination']) if kept_existing_files else '')
        if item.get('kind')=='tv' and context.get('season') is not None and context.get('episode') is not None:
            target_label=f"{item.get('title') or 'TV'} • S{int(context.get('season') or 0):02d}E{int(context.get('episode') or 0):02d}" + (f" • {context.get('episode_title')}" if context.get('episode_title') else '')
        elif item.get('kind')=='tv' and context.get('season') is not None:
            target_label=f"{item.get('title') or 'TV'} • Season {int(context.get('season') or 0)}"
        else:
            target_label=str(item.get('title') or 'Movie')
        all_final=imported+kept_existing_files
        return {'ok':True,'destination':primary,'destinations':[x['destination'] for x in all_final],'files':imported,'kept_files':kept_existing_files,'quality':str((all_final[0].get('quality') if all_final else context.get('release_quality')) or 'Unknown'),'kind':item.get('kind'),'item_id':'' if one_time else item.get('id'),'one_time':one_time,'target_label':target_label,'release_title':str(context.get('release_title') or ''),'release_size':int(context.get('release_size') or 0),'verified':True,'imported_count':len(imported),'season_pack':bool(context.get('season_pack')),'inspection':inspections,'needs_attention_count':len(attention),'cleanup_safe':len(attention)==0,'kept_existing':sum(1 for e in entries if e.get('action') in {'DUPLICATE','KEEP_EXISTING'})}

    def _aired(self,d:str):
        if not d: return False
        return d <= datetime.now().date().isoformat()

    def _movie_wanted_date(self, item:dict[str,Any], cfg:dict[str,Any]) -> tuple[str,str]:
        policy=str(cfg.get('automatic_movie_availability') or 'digital_physical')
        theatrical=_date(item.get('theatrical_release_date')) or _date(item.get('release_date'))
        digital=_date(item.get('digital_release_date')); physical=_date(item.get('physical_release_date')); available=_date(item.get('availability_date'))
        if policy=='theatrical': return theatrical,'theatrical'
        home=min([x for x in (available,digital,physical) if x],default='')
        if home: return home,'home'


        if theatrical:
            try:
                td=datetime.fromisoformat(theatrical).date()
                if (datetime.now().date()-td).days>=120: return theatrical,'assumed_home'
            except Exception: pass
        return '', 'waiting_home_release'

    def _movie_available(self, item:dict[str,Any]) -> bool:
        """Return whether a movie is currently eligible to be wanted.

        Discover uses this when decorating TMDB cards with Automation library state.
        Keep it on the exact same availability policy as the Automation Wanted view so
        navigation between the two surfaces cannot disagree or raise an attribute error.
        """
        wanted_date, _availability = self._movie_wanted_date(item, self.public_config())
        return bool(wanted_date and self._aired(wanted_date))

    def wanted(self):
        lib=self._library(); profiles={str(p.get('id')):p for p in self._profiles()}; cfg=self.public_config(); missing=[];upgrades=[]
        for item in lib:
            if not item.get('monitored',True): continue
            if str(item.get('library_root_status') or '')=='offline':

                continue
            profile=profiles.get(str(item.get('quality_profile_id'))) or self._profiles()[0]
            cutoff=str(profile.get('cutoff') or '')
            if item.get('kind')=='movie':
                wanted_date,availability=self._movie_wanted_date(item,cfg)
                released=self._aired(wanted_date)
                if released:
                    if not item.get('movie_file'):
                        row={'item_id':item['id'],'kind':'movie','title':item['title'],'year':item.get('year'),'date':wanted_date,'availability':availability,'label':item['title'],'cutoff':cutoff,'reason_code':'missing','reason_label':'Missing movie file','reason_detail':'The movie is available under your release policy but no library file is present.'}; row['target_key']=self._auto_target_key(row=row); missing.append(row)
                    elif str(item.get('monitor_mode') or 'movie')!='missing' and not item['movie_file'].get('cutoff_met'):
                        row={'item_id':item['id'],'kind':'movie','title':item['title'],'date':wanted_date,'availability':availability,'current_quality':item['movie_file'].get('quality'),'cutoff':cutoff,'label':item['title'],'reason_code':'upgrade','reason_label':'Quality below cutoff','reason_detail':f"Current {item['movie_file'].get('quality') or 'Unknown'} has not reached {cutoff or 'the profile cutoff'}."}; row['target_key']=self._auto_target_key(row=row); upgrades.append(row)
            else:
                for season in item.get('seasons') or []:
                    if not season.get('monitored',True): continue
                    for ep in season.get('episodes') or []:
                        if not ep.get('monitored',True) or not self._aired(str(ep.get('air_date') or '')): continue
                        row={'item_id':item['id'],'kind':'tv','title':item['title'],'season':season.get('season_number'),'episode':ep.get('episode_number'),'episode_name':ep.get('name'),'date':ep.get('air_date'),'label':f"{item['title']} S{int(season.get('season_number',0)):02d}E{int(ep.get('episode_number',0)):02d}",'cutoff':cutoff,'reason_code':'missing' if not ep.get('has_file') else 'upgrade','reason_label':'Missing episode' if not ep.get('has_file') else 'Quality below cutoff','reason_detail':'Released monitored episode has no library file.' if not ep.get('has_file') else f"Current {ep.get('file_quality') or 'Unknown'} has not reached {cutoff or 'the profile cutoff'}."}
                        row['target_key']=self._auto_target_key(row=row)
                        if not ep.get('has_file'): missing.append(row)
                        elif str(item.get('monitor_mode') or 'all')!='missing' and not ep.get('cutoff_met'): upgrades.append({**row,'current_quality':ep.get('file_quality')})
        missing.sort(key=lambda x:(x.get('date') or '',x.get('label') or '')); upgrades.sort(key=lambda x:x.get('label') or '')
        return {'missing':missing,'upgrades':upgrades}

    def history(self, limit:int=200, item_id:str=''):
        rows=[]; wanted_id=str(item_id or '')
        for rec in self._activity():
            if not isinstance(rec,dict): continue
            details=rec.get('details') if isinstance(rec.get('details'),dict) else {}
            if wanted_id and str(details.get('item_id') or '')!=wanted_id: continue
            rows.append(rec)
            if len(rows)>=max(1,min(500,int(limit or 200))): break
        return rows

    def calendar(self, days=400, history_days=45):
        """Return the monitored release calendar with enough context for Guide/Month UI.

        The previous calendar only exposed future labels.  The richer calendar keeps a
        short recent-history window so the current month can show what already aired or
        imported, while retaining roughly a year of future release data.  It intentionally
        derives status from the same library state used by Wanted so Calendar and Wanted
        cannot disagree about missing/upgrade/imported media.
        """
        now_date=datetime.now().date(); today=now_date.isoformat(); events=[]; cfg=self.public_config()
        start=(now_date-timedelta(days=max(0,int(history_days or 0)))).isoformat()
        end=(now_date+timedelta(days=max(30,int(days or 400)))).isoformat()
        for item in self._library():
            if not item.get('monitored',True): continue
            poster=str(item.get('poster_url') or ''); backdrop=str(item.get('backdrop_url') or '')
            common={'item_id':item.get('id'),'title':str(item.get('title') or 'Untitled'),'poster_url':poster,'backdrop_url':backdrop,'overview':str(item.get('overview') or ''),'year':item.get('year'),'rating':item.get('rating'),'network':str(item.get('network') or ''),'monitor_mode':str(item.get('monitor_mode') or '')}
            if item.get('kind')=='movie':
                d,availability=self._movie_wanted_date(item,cfg)
                if not d or d<start or d>end: continue
                mf=item.get('movie_file') if isinstance(item.get('movie_file'),dict) else None
                has_file=bool(mf); cutoff_met=bool((mf or {}).get('cutoff_met')) if has_file else False
                upgrade=bool(has_file and str(item.get('monitor_mode') or 'movie')!='missing' and not cutoff_met)
                if upgrade: status='upgrade'; status_label='Upgrade wanted'
                elif has_file: status='imported'; status_label='Imported'
                elif d<today: status='missing'; status_label='Missing'
                elif d==today: status='today'; status_label='Available today'
                else: status='upcoming'; status_label='Upcoming'
                release_label='Home release' if availability in {'home','assumed_home'} else 'Release'
                events.append({**common,'date':d,'kind':'movie','availability':availability,'availability_label':release_label,'label':str(item.get('title') or 'Untitled'),'subtitle':release_label,'status':status,'status_label':status_label,'has_file':has_file,'cutoff_met':cutoff_met,'quality':str((mf or {}).get('quality') or '')})
            else:
                for season in item.get('seasons') or []:
                    if not season.get('monitored',True): continue
                    sn=int(season.get('season_number') or 0)
                    for ep in season.get('episodes') or []:
                        d=str(ep.get('air_date') or '')[:10]
                        if not ep.get('monitored',True) or not d or d<start or d>end: continue
                        en=int(ep.get('episode_number') or 0); has_file=bool(ep.get('has_file')); cutoff_met=bool(ep.get('cutoff_met')) if has_file else False
                        upgrade=bool(has_file and str(item.get('monitor_mode') or 'all')!='missing' and not cutoff_met)
                        if upgrade: status='upgrade'; status_label='Upgrade wanted'
                        elif has_file: status='imported'; status_label='Imported'
                        elif d<today: status='missing'; status_label='Missing'
                        elif d==today: status='today'; status_label='Airs today'
                        else: status='upcoming'; status_label='Upcoming'
                        code=f'S{sn:02d}E{en:02d}'; name=str(ep.get('name') or '')
                        events.append({**common,'date':d,'kind':'tv','season':sn,'episode':en,'episode_name':name,'label':str(item.get('title') or 'Untitled'),'subtitle':f'{code}{" — "+name if name else ""}','status':status,'status_label':status_label,'has_file':has_file,'cutoff_met':cutoff_met,'quality':str(ep.get('file_quality') or ''),'air_date':d})
        events.sort(key=lambda x:(x.get('date') or '',x.get('kind') or '',x.get('label') or '',int(x.get('season') or 0),int(x.get('episode') or 0)))
        return events[:1000]

    def sidebar_counts(self):
        """Return only the small count payload needed by persistent navigation.

        Startup should not need to build the full Automation summary (calendar,
        history, runtime health, indexer details, etc.) just to paint TV/Movie/
        Wanted badges. Keep this derived from the same library/Wanted rules so the
        sidebar cannot disagree with the full Automation view.
        """
        warnings=[]
        try:
            lib=self._library()
            if not isinstance(lib,list): lib=[]
        except Exception as exc:
            lib=[];warnings.append(f'Library could not be read: {exc}')
        try:
            wanted=self.wanted()
        except Exception as exc:
            wanted={'missing':[],'upgrades':[]};warnings.append(f'Wanted view could not be calculated: {exc}')
        return {
            'tv':sum(isinstance(x,dict) and x.get('kind')=='tv' for x in lib),
            'movies':sum(isinstance(x,dict) and x.get('kind')=='movie' for x in lib),
            'missing':len(wanted.get('missing') or []),
            'upgrades':len(wanted.get('upgrades') or []),
            'loaded':True,
            'warnings':warnings,
        }

    def summary(self):
        warnings=[]
        try:
            lib=self._library()
            if not isinstance(lib,list): lib=[]
        except Exception as exc:
            lib=[];warnings.append(f'Library could not be read: {exc}')
        try:
            idx=self.public_indexers()
        except Exception as exc:
            idx=[];warnings.append(f'Indexers could not be read: {exc}')
        try:
            profiles=self._profiles()
        except Exception as exc:
            profiles=list(DEFAULT_PROFILES);warnings.append(f'Quality profiles could not be read: {exc}')
        try:
            config=self.public_config()
        except Exception as exc:
            config={'tv_roots':[],'movie_roots':[],'metadata_provider':'keyless','metadata_tv':{'provider':'TVmaze','configured':True,'key_required':False},'metadata_movies':{'provider':'Wikidata','configured':True,'key_required':False},'tmdb_configured':False,'tmdb_optional':True,'automatic_grab_enabled':False,'automatic_backlog_enabled':False,'automatic_upgrades_enabled':False,'automatic_season_packs_enabled':True,'automatic_feed_enabled':True,'automatic_feed_interval_minutes':5,'automatic_smart_retry_enabled':True,'automatic_quiet_hours_enabled':False,'automatic_quiet_start':'01:00','automatic_quiet_end':'07:00','automatic_notifications_enabled':False,'automatic_search_interval_minutes':15,'automatic_retry_minutes':60,'automatic_release_delay_minutes':5,'automatic_queue_depth':25,'automatic_metadata_refresh_hours':6,'automatic_library_scan_minutes':30,'automatic_movie_availability':'digital_physical'};warnings.append(f'Automation config could not be read: {exc}')
        try:
            wanted=self.wanted()
        except Exception as exc:
            wanted={'missing':[],'upgrades':[]};warnings.append(f'Wanted view could not be calculated: {exc}')
        try:
            calendar=self.calendar()
        except Exception as exc:
            calendar=[];warnings.append(f'Calendar could not be calculated: {exc}')
        try:
            activity=self._activity()[:100]
        except Exception:
            activity=[]
        try:
            automatic=self.automatic_status()
        except Exception as exc:
            automatic={'enabled':bool(config.get('automatic_grab_enabled')),'running':False,'last_error':str(exc)}
        try:
            health=self.automation_health()
        except Exception as exc:
            health={'error':str(exc),'roots':[],'blacklists':[]}
        return {'library':lib,'config':config,'profiles':profiles,'indexers':idx,'wanted':wanted,'calendar':calendar,'activity':activity,'history':activity,'automatic':automatic,'health':health,'warnings':warnings,'counts':{'tv':sum(isinstance(x,dict) and x.get('kind')=='tv' for x in lib),'movies':sum(isinstance(x,dict) and x.get('kind')=='movie' for x in lib),'missing':len(wanted.get('missing') or []),'upgrades':len(wanted.get('upgrades') or []),'indexers':sum(isinstance(x,dict) and x.get('enabled',True) for x in idx)}}

    def save_profile(self,data):
        with self.lock:
            profiles=self._profiles(); ident=str(data.get('id') or secrets.token_hex(8)); name=str(data.get('name') or '').strip()
            if not name: raise ValueError('Profile name is required')
            qualities=[str(x).strip() for x in data.get('qualities') or [] if str(x).strip()]
            if not qualities: raise ValueError('Add at least one allowed quality')
            cutoff=str(data.get('cutoff') or qualities[0]); cfs=[]
            for cf in data.get('custom_formats') or []:
                if not isinstance(cf,dict): continue
                cfs.append({'name':str(cf.get('name') or 'Preference'),'contains':[str(x).strip() for x in cf.get('contains') or [] if str(x).strip()],'score':int(cf.get('score',0) or 0)})

            try: min_size_mb=max(0,float(data.get('min_size_mb') or 0))
            except Exception: min_size_mb=0
            try: max_size_gb=max(0,float(data.get('max_size_gb') or 0))
            except Exception: max_size_gb=0
            reject_terms=[str(x).strip() for x in data.get('reject_terms') or [] if str(x).strip()][:60]
            preferred_groups=[str(x).strip() for x in data.get('preferred_groups') or [] if str(x).strip()][:60]
            rec={'id':ident,'name':name,'qualities':qualities,'cutoff':cutoff,'min_size_mb':min_size_mb,'max_size_gb':max_size_gb,'reject_terms':reject_terms,'preferred_groups':preferred_groups,'custom_formats':cfs}
            old=next((i for i,x in enumerate(profiles) if str(x.get('id'))==ident),None)
            if old is None: profiles.append(rec)
            else: profiles[old]=rec
            _write(self.profiles_file,profiles);return rec

    def delete_profile(self,ident):
        with self.lock:
            profiles=self._profiles()
            if len(profiles)<=1: raise ValueError('At least one quality profile is required')
            profiles=[p for p in profiles if str(p.get('id'))!=str(ident)];_write(self.profiles_file,profiles);return {'ok':True}

    def public_indexers(self):
        out=[]
        for x in self._indexers():
            out.append({k:v for k,v in x.items() if k!='api_key_protected'}|{'api_key_configured':bool(x.get('api_key_protected'))})
        return out

    def save_indexer(self,data):
        with self.lock:
            items=self._indexers();ident=str(data.get('id') or secrets.token_hex(8));url=str(data.get('url') or '').strip().rstrip('/')
            if not url.startswith(('http://','https://')): raise ValueError('Indexer URL must start with http:// or https://')
            rec=next((dict(x) for x in items if str(x.get('id'))==ident),{})
            rec.update({'id':ident,'name':str(data.get('name') or '').strip() or urllib.parse.urlparse(url).netloc,'url':url,'enabled':bool(data.get('enabled',True)),'categories_tv':str(data.get('categories_tv') or '5000'),'categories_movies':str(data.get('categories_movies') or '2000')})
            key=str(data.get('api_key') or '').strip()
            if key: rec['api_key_protected']=self.protect_secret(key)
            if not rec.get('api_key_protected') and not data.get('allow_empty_key'): raise ValueError('Indexer API key is required')
            pos=next((i for i,x in enumerate(items) if str(x.get('id'))==ident),None)
            if pos is None: items.append(rec)
            else: items[pos]=rec
            _write(self.indexers_file,items);return {k:v for k,v in rec.items() if k!='api_key_protected'}|{'api_key_configured':True}

    def delete_indexer(self,ident):
        with self.lock:
            items=[x for x in self._indexers() if str(x.get('id'))!=str(ident)];_write(self.indexers_file,items);return {'ok':True}

    def _indexer_url(self,idx, params):
        base=str(idx.get('url') or '').rstrip('/')
        if not base.endswith('/api'): base += '/api'
        q=dict(params); key=self.unprotect_secret(str(idx.get('api_key_protected') or ''))
        if key: q['apikey']=key
        return base+'?'+urllib.parse.urlencode(q)

    def test_indexer(self,ident):
        idx=next((x for x in self._indexers() if str(x.get('id'))==str(ident)),None)
        if not idx: raise ValueError('Indexer was not found')
        url=self._indexer_url(idx,{'t':'caps'})
        started=time.perf_counter()
        raw=self._http_bytes_deadline(url,7.0,{'User-Agent':f'NewzDeck/{self.version}','Accept':'application/xml,text/xml,*/*'},2*1024*1024)
        root=ET.fromstring(raw)
        return {'ok':True,'latency_ms':round((time.perf_counter()-started)*1000,1),'server':root.tag.split('}')[-1],'name':idx.get('name')}

    def _parse_newznab_items(self, raw:bytes, idx:dict[str,Any]) -> list[dict[str,Any]]:
        root=ET.fromstring(raw);out=[]
        for node in root.iter():
            if node.tag.split('}')[-1]!='item': continue
            vals={}; attrs={}
            for c in list(node):
                local=c.tag.split('}')[-1]
                if local=='attr': attrs[str(c.attrib.get('name') or '').casefold()]=str(c.attrib.get('value') or '')
                elif local=='enclosure': vals['enclosure_url']=c.attrib.get('url');vals['enclosure_length']=c.attrib.get('length')
                else: vals[local]=c.text or ''
            title=str(vals.get('title') or '').strip(); link=str(vals.get('enclosure_url') or vals.get('link') or vals.get('guid') or '').strip()
            if not title or not link: continue
            size=int(attrs.get('size') or vals.get('enclosure_length') or 0) if str(attrs.get('size') or vals.get('enclosure_length') or '0').isdigit() else 0
            ts=0
            try: ts=email.utils.parsedate_to_datetime(str(vals.get('pubDate') or '')).timestamp()
            except Exception: pass
            out.append({'title':title,'download_url':link,'size':size,'published':ts,'indexer_id':idx.get('id'),'indexer':idx.get('name'),'guid':str(vals.get('guid') or link),'grabs':int(attrs.get('grabs','0')) if str(attrs.get('grabs','0')).isdigit() else 0})
        return out

    def _search_indexer(self,idx,item,season=None,episode=None):
        kind=item.get('kind')
        category=idx.get('categories_tv') if kind=='tv' else idx.get('categories_movies')
        title=str(item.get('title') or '').strip()
        headers={'User-Agent':f'NewzDeck/{self.version}','Accept':'application/rss+xml,application/xml,text/xml,*/*'}

        def request(params:dict[str,Any], timeout:float) -> list[dict[str,Any]]:
            url=self._indexer_url(idx,params)
            raw=self._http_bytes_deadline(url,timeout,headers,12*1024*1024)
            return self._parse_newznab_items(raw,idx)

        primary={'t':'tvsearch' if kind=='tv' else 'movie','q':title,'limit':100,'cat':category}
        if kind=='tv' and season is not None:
            primary['season']=int(season)
            if episode is not None: primary['ep']=int(episode)
        if kind=='movie' and item.get('year'): primary['year']=item['year']

        primary_error=None
        try:
            rows=request(primary,INDEXER_PRIMARY_TIMEOUT)
            if rows:
                return rows
        except urllib.error.HTTPError as exc:
            # Authentication/permission failures will not improve with a generic
            # query and should be reported immediately rather than duplicated.
            if int(getattr(exc,'code',0) or 0) in {401,403}:
                raise
            primary_error=exc
        except (urllib.error.URLError,TimeoutError,OSError,ValueError,ET.ParseError) as exc:
            primary_error=exc

        # Newznab implementations vary considerably in tvsearch/movie support.
        # A bounded generic search is a compatibility fallback and also prevents a
        # slow specialized endpoint from making Interactive Search unusable.
        generic_title=title
        if kind=='tv' and season is not None:
            generic_title += f' S{int(season):02d}'
            if episode is not None: generic_title += f'E{int(episode):02d}'
        elif kind=='movie' and item.get('year'):
            generic_title += f' {item.get("year")}'
        generic={'t':'search','q':generic_title,'limit':100,'cat':category}
        try:
            return request(generic,INDEXER_FALLBACK_TIMEOUT)
        except Exception as fallback_error:
            if primary_error is not None:
                raise TimeoutError(f'Specialized search failed ({primary_error}); generic fallback also failed ({fallback_error})') from fallback_error
            raise

    def _recent_indexer_releases(self, idx:dict[str,Any]) -> list[dict[str,Any]]:
        cats=[]
        for field in ('categories_tv','categories_movies'):
            cats.extend(x.strip() for x in str(idx.get(field) or '').split(',') if x.strip())
        params={'t':'search','limit':100}
        if cats: params['cat']=','.join(dict.fromkeys(cats))
        url=self._indexer_url(idx,params)
        raw=self._http_bytes_deadline(url,9.0,{'User-Agent':f'NewzDeck/{self.version}','Accept':'application/rss+xml,application/xml,text/xml,*/*'},12*1024*1024)
        return self._parse_newznab_items(raw,idx)

    def _poll_release_feed(self, rt:dict[str,Any], cfg:dict[str,Any], *, force:bool=False) -> list[dict[str,Any]]:
        if not bool(cfg.get('automatic_feed_enabled',True)):
            self.release_feed_cache=[]; self.release_feed_cache_ts=0.0
            return []
        now=time.time(); interval=max(2,int(cfg.get('automatic_feed_interval_minutes') or 5))*60
        if not force and self.release_feed_cache and now-self.release_feed_cache_ts<interval:
            return list(self.release_feed_cache)
        enabled=[x for x in self._indexers() if x.get('enabled',True)]
        rows=[]; errors=[]
        if enabled:
            with ThreadPoolExecutor(max_workers=min(6,len(enabled)),thread_name_prefix='newznab-feed') as pool:
                jobs={pool.submit(self._recent_indexer_releases,idx):idx for idx in enabled}
                for fut in as_completed(jobs):
                    idx=jobs[fut]
                    try: rows.extend(fut.result())
                    except Exception as exc: errors.append(f"{idx.get('name')}: {exc}")
        cutoff=now-48*3600; unique={}
        for row in rows:
            published=float(row.get('published') or 0)
            if published and published<cutoff: continue
            key=str(row.get('guid') or row.get('title') or '').casefold()
            old=unique.get(key)
            if old is None or int(row.get('grabs') or 0)>int(old.get('grabs') or 0): unique[key]=row
        rows=sorted(unique.values(),key=lambda x:(float(x.get('published') or 0),int(x.get('grabs') or 0)),reverse=True)[:1000]
        self.release_feed_cache=list(rows); self.release_feed_cache_ts=now
        rt['last_feed_poll_ts']=now; rt['last_feed_count']=len(rows); rt['last_feed_errors']=errors[:8]
        return list(rows)

    def _feed_candidates_for_target(self,item:dict[str,Any],row:dict[str,Any],profile:dict[str,Any],feed_rows:list[dict[str,Any]],rt:dict[str,Any],rec:dict[str,Any],now:float,release_delay:int) -> list[dict[str,Any]]:
        attempted={str(x.get('guid') or '').casefold() for x in rec.get('attempted_releases') or [] if isinstance(x,dict) and x.get('guid') and now-float(x.get('ts') or 0)<12*3600}
        blacklist=[x for x in rec.get('blacklist') or [] if isinstance(x,dict)]
        blocked_guid={str(x.get('guid') or '').casefold() for x in blacklist if x.get('guid')}; blocked_title={str(x.get('title') or '').casefold() for x in blacklist if x.get('title')}
        current=str(row.get('current_quality') or self._target_current_quality(item,row.get('season'),row.get('episode')) or 'Unknown')
        candidates=[]
        for base in feed_rows:
            title=str(base.get('title') or '')
            if not title or not _slug_match(title,str(item.get('title') or ''),item.get('year') if item.get('kind')=='movie' else None): continue
            guid=str(base.get('guid') or base.get('download_url') or '').casefold()
            if (guid and guid in attempted) or (guid and guid in blocked_guid) or title.casefold() in blocked_title: continue
            published=float(base.get('published') or 0)
            if release_delay and published and now-published<release_delay: continue
            rel=dict(base)
            rel.update(self._evaluate_release(title,int(rel.get('size') or 0),profile,item=item,season=row.get('season'),episode=row.get('episode'),current_quality=current))
            if not self._auto_release_matches(item,row,rel,profile,upgrade=row.get('auto_type')=='upgrade'): continue
            penalty=self._indexer_penalty(rt,str(rel.get('indexer') or ''),now)
            rel.update({'item_id':str(item.get('id') or ''),'media_kind':str(item.get('kind') or ''),'season':row.get('season'),'episode':row.get('episode'),'episode_title':str(row.get('episode_name') or ''),'season_pack':bool(row.get('season_pack')),'pack_episode_numbers':list(row.get('pack_episode_numbers') or []),'current_quality':current,'automatic_eligible':True,'automation_indexer_penalty':penalty,'automation_effective_score':int(rel.get('score') or 0)-penalty,'decision':'FEED MATCH'})
            candidates.append(rel)
        return sorted(candidates,key=lambda x:(int(x.get('automation_effective_score') or -99999),float(x.get('published') or 0)),reverse=True)


    def search_releases(self,item_id,season=None,episode=None):
        item=next((x for x in self._library() if str(x.get('id'))==str(item_id)),None)
        if not item: raise ValueError('Library item was not found')
        profile=next((p for p in self._profiles() if str(p.get('id'))==str(item.get('quality_profile_id'))),self._profiles()[0])
        season_pack=bool(item.get('kind')=='tv' and season is not None and episode is None)
        current_quality=self._target_current_quality(item,season,episode)
        releases=[];errors=[]
        enabled=[idx for idx in self._indexers() if idx.get('enabled',True)]
        if enabled:
            pool=ThreadPoolExecutor(max_workers=min(12,len(enabled)),thread_name_prefix='newznab')
            jobs={pool.submit(self._search_indexer,idx,item,season,episode):idx for idx in enabled}
            done,pending=wait(jobs,timeout=_indexer_search_wall_timeout())
            for fut in done:
                idx=jobs[fut]
                try:
                    rows=fut.result()
                    for r in rows:
                        # Newznab category/search implementations may return broad matches.
                        # Never let an unrelated show/movie enter the candidate table merely
                        # because it shares SxxEyy or a release-group substring.
                        if not _slug_match(str(r.get('title') or ''),str(item.get('title') or ''),item.get('year') if item.get('kind')=='movie' else None):
                            continue
                        ev=self._evaluate_release(r['title'],r['size'],profile,item=item,season=season,episode=episode,current_quality=current_quality)
                        r.update(ev); releases.append(r)
                except Exception as exc: errors.append({'indexer':idx.get('name'),'error':str(exc)})
            for fut in pending:
                idx=jobs[fut]; fut.cancel(); errors.append({'indexer':idx.get('name'),'error':f'Timed out after {_indexer_search_wall_timeout():g} seconds; results from responsive indexers were returned.'})
            pool.shutdown(wait=False,cancel_futures=True)
        unique={}
        for r in releases:
            key=(r.get('guid') or r.get('title','')).casefold(); old=unique.get(key)
            if old is None or int(r.get('score',0))>int(old.get('score',0)): unique[key]=r
        releases=list(unique.values()); episode_title=''; pack_episode_numbers=[]
        if item.get('kind')=='tv' and season is not None:
            sn=int(season); sr=next((x for x in item.get('seasons',[]) if int(x.get('season_number',0) or 0)==sn),None)
            if episode is not None:
                en=int(episode); ep=next((x for x in (sr or {}).get('episodes',[]) if int(x.get('episode_number',0) or 0)==en),None); episode_title=str((ep or {}).get('name') or '')
            else:
                today=datetime.now().date().isoformat()
                pack_episode_numbers=sorted(int(ep.get('episode_number') or 0) for ep in (sr or {}).get('episodes',[]) if bool(ep.get('monitored',True)) and int(ep.get('episode_number') or 0)>0 and str(ep.get('air_date') or '') and str(ep.get('air_date') or '')<=today and not bool(ep.get('has_file')))
        target_ctx={'item_id':str(item.get('id') or ''),'kind':str(item.get('kind') or ''),'season':season,'episode':episode,'season_pack':season_pack}
        target_key=self._auto_target_key(context=target_ctx)
        rt=self._auto_runtime()
        # Reconcile terminal failures on every Interactive Search as well as the
        # unattended scheduler. This makes a manually grabbed bad post immediately
        # visible the next time the user searches for that same episode/movie.
        if self._sync_automatic_failures(rt): self._save_auto_runtime(rt)
        rec=((rt.get('targets') or {}).get(target_key) or {}) if target_key else {}
        blacklisted=[x for x in rec.get('blacklist') or [] if isinstance(x,dict)]
        bg={str(x.get('guid') or '').casefold() for x in blacklisted if x.get('guid')}; bt={str(x.get('title') or '').casefold() for x in blacklisted if x.get('title')}
        row_ctx={'season':season,'episode':episode,'season_pack':season_pack,'current_quality':current_quality}
        for r in releases:
            r['item_id']=str(item.get('id') or ''); r['media_kind']=str(item.get('kind') or '')
            r['season']=int(season) if season is not None else None; r['episode']=int(episode) if episode is not None else None
            r['season_pack']=season_pack; r['pack_episode_numbers']=pack_episode_numbers
            r['episode_title']=episode_title; r['current_quality']=current_quality; r['target_key']=target_key
            guid=str(r.get('guid') or r.get('download_url') or '').casefold(); title=str(r.get('title') or '').casefold()
            blocked=next((x for x in blacklisted if ((guid and str(x.get('guid') or '').casefold()==guid) or (not guid and str(x.get('title') or '').casefold()==title) or str(x.get('title') or '').casefold()==title)),None)
            r['blacklisted']=bool(blocked)
            if r['blacklisted']:
                failure_source=str((blocked or {}).get('source') or '')
                failure_reason=str((blocked or {}).get('reason') or 'Release is blacklisted for this target')
                r['blacklist_reason']=failure_reason
                r['blacklist_failed']=failure_source=='download_failure' or bool(str((blocked or {}).get('collection_id') or '')) or (str((blocked or {}).get('error_code') or '') not in {'','manual'})
                r['blacklist_failed_ts']=float((blocked or {}).get('failed_ts') or 0)
                r['accepted']=False; r['decision']='FAILED' if r['blacklist_failed'] else 'BLACKLISTED'; r['rejections']=list(r.get('rejections') or [])+[('Previous download failed: '+failure_reason) if r['blacklist_failed'] else 'Release is blacklisted for this target']
            r['automatic_eligible']=bool(r.get('accepted')) and self._auto_release_matches(item,row_ctx,r,profile,upgrade=(not season_pack and current_quality not in {'','Unknown'}))
            if r.get('accepted') and not r['automatic_eligible']:
                r['decision']='MANUAL ONLY'; r['reasons']=list(r.get('reasons') or [])+['Passes profile, but unattended safety rules require manual choice']
            r['effective_score']=int(r.get('score') or 0)-self._indexer_penalty(rt,str(r.get('indexer') or ''))
        releases=sorted(releases,key=lambda x:(bool(x.get('automatic_eligible')),bool(x.get('accepted')),int(x.get('effective_score',-9999)),int(x.get('published',0))),reverse=True)
        recommended=next((r for r in releases if r.get('automatic_eligible')),None)
        if recommended: recommended['recommended']=True; recommended['decision']='RECOMMENDED'
        for i,r in enumerate(releases,1): r['rank']=i
        failed_releases=[dict(x) for x in blacklisted if str(x.get('source') or '')=='download_failure' or bool(str(x.get('collection_id') or '')) or str(x.get('error_code') or '') not in {'','manual'}]
        failed_releases=sorted(failed_releases,key=lambda x:float(x.get('failed_ts') or 0),reverse=True)[:12]
        return {'item':item,'profile':profile,'current_quality':current_quality,'target_key':target_key,'season_pack':season_pack,'pack_episode_numbers':pack_episode_numbers,'recommended_guid':str((recommended or {}).get('guid') or ''),'releases':releases[:300],'errors':errors,'searched_indexers':len(enabled),'blacklist_count':len(blacklisted),'failed_releases':failed_releases}

    def release_storage_plan(self,item:dict[str,Any],release_size:int) -> dict[str,Any]:
        size=max(0,int(release_size or 0)); root_need=self._storage_requirement(size,staging=False); staging_need=self._storage_requirement(size,staging=True)
        root=self._resolve_root(item,required_bytes=root_need)
        root_free=self._disk_free(root); staging_path=None; staging_free=0
        try:
            snap=self.download_manager.snapshot(); staging_path=Path(str(snap.get('folder') or '')).expanduser() if snap.get('folder') else None; staging_free=self._disk_free(staging_path)
        except Exception: pass
        return {'root':str(root or ''),'root_free':root_free,'root_required':root_need,'staging':str(staging_path or ''),'staging_free':staging_free,'staging_required':staging_need,'ok_root':bool(root and root.exists() and (not size or root_free>=root_need)),'ok_staging':bool(not size or not staging_path or staging_free>=staging_need)}

    def _target_current_quality(self,item:dict[str,Any],season=None,episode=None) -> str:
        if item.get('kind')=='movie': return str((item.get('movie_file') or {}).get('quality') or 'Unknown')
        if season is not None and episode is None: return 'Multiple / season pack'
        try: sn,en=int(season),int(episode)
        except Exception: return 'Unknown'
        sr=next((x for x in item.get('seasons') or [] if int(x.get('season_number') or 0)==sn),None)
        ep=next((x for x in (sr or {}).get('episodes') or [] if int(x.get('episode_number') or 0)==en),None)
        return str((ep or {}).get('file_quality') or 'Unknown')

    def _fetch_release_nzb(self,data):
        """Fetch a Newznab NZB through several safe, same-indexer authentication forms.

        Search RSS feeds are inconsistent about their enclosure URLs: modern servers may
        use apikey=, older Newznab links often use r=, and the canonical API always
        supports t=get&id=<guid>&apikey=. Never copy credentials to another host.
        """
        url=str(data.get('download_url') or '').strip()
        if not url.startswith(('http://','https://')): raise ValueError('Release download URL is invalid')
        idx_id=str(data.get('indexer_id') or '').strip(); idx_name=str(data.get('indexer') or '').strip()
        idx=next((x for x in self._indexers() if (idx_id and str(x.get('id') or '')==idx_id) or (idx_name and str(x.get('name') or '')==idx_name)),None)
        headers={'User-Agent':f'NewzDeck/{self.version}','Accept':'application/x-nzb,application/xml,text/xml,*/*'}

        def fetch(target):
            req=urllib.request.Request(target,headers=headers)
            with urllib.request.urlopen(req,timeout=60) as r:
                length=int(r.headers.get('Content-Length') or 0)
                if length>100*1024*1024: raise ValueError('Indexer NZB is larger than 100 MB')
                raw=r.read(100*1024*1024+1)
            if len(raw)>100*1024*1024: raise ValueError('Indexer NZB is larger than 100 MB')
            # Newznab semantic errors are sometimes returned with HTTP 200.
            head=raw[:65536].lstrip().lower()
            if b'<error' in head and b'<nzb' not in head:
                try:
                    eroot=ET.fromstring(raw); code=str(eroot.attrib.get('code') or ''); desc=str(eroot.attrib.get('description') or 'Indexer rejected NZB request')
                except Exception:
                    code=''; desc='Indexer rejected NZB request'
                raise RuntimeError(f"Indexer NZB fetch failed for {idx_name or 'configured indexer'}: {desc}{' (code '+code+')' if code else ''}")
            return raw

        attempts=[('release URL',url)]
        key=''; base=''
        if idx:
            try: key=self.unprotect_secret(str(idx.get('api_key_protected') or '')).strip()
            except Exception: key=''
            base=str(idx.get('url') or '').strip()

        def authority(parsed):
            host=(parsed.hostname or '').casefold(); port=parsed.port or (443 if parsed.scheme.casefold()=='https' else 80)
            return host,port

        src=urllib.parse.urlparse(url); configured=urllib.parse.urlparse(base) if base else None
        same_host=bool(configured and authority(src)==authority(configured))
        if key and same_host:
            q=urllib.parse.parse_qs(src.query,keep_blank_values=True)
            if q.get('apikey')!=[key]:
                q1=dict(q); q1['apikey']=[key]
                attempts.append(('release URL + apikey',urllib.parse.urlunparse(src._replace(query=urllib.parse.urlencode(q1,doseq=True)))))
            if q.get('r')!=[key]:
                q2=dict(q); q2['r']=[key]
                attempts.append(('release URL + r key',urllib.parse.urlunparse(src._replace(query=urllib.parse.urlencode(q2,doseq=True)))))

            # Canonical Newznab GET is the most portable fallback. Recover an ID from
            # the result GUID or from common enclosure query/path forms.
            ids=[]
            guid=str(data.get('guid') or '').strip()
            if guid and not guid.startswith(('http://','https://')): ids.append(guid)
            for name in ('id','guid'):
                for value in q.get(name,[]):
                    value=str(value or '').strip()
                    if value and value not in ids: ids.append(value)
            if guid.startswith(('http://','https://')):
                gp=urllib.parse.urlparse(guid); gq=urllib.parse.parse_qs(gp.query)
                for name in ('id','guid'):
                    for value in gq.get(name,[]):
                        value=str(value or '').strip()
                        if value and value not in ids: ids.append(value)
                tail=Path(gp.path).name.strip()
                if re.fullmatch(r'[A-Za-z0-9._-]{12,160}',tail or '') and tail not in ids: ids.append(tail)
            tail=Path(src.path).name.strip()
            if re.fullmatch(r'[A-Za-z0-9._-]{12,160}',tail or '') and tail not in ids: ids.append(tail)
            for ident in ids[:4]:
                try: canonical=self._indexer_url(idx,{'t':'get','id':ident})
                except Exception: continue
                attempts.append((f'Newznab GET ({ident[:12]}…)',canonical))

        # De-duplicate while preserving strongest/most natural order.
        unique=[]; seen=set()
        for label,target in attempts:
            if target in seen: continue
            seen.add(target); unique.append((label,target))

        def transient_kind(exc):
            text=str(exc or '').casefold()
            if any(x in text for x in ('winerror 10054','errno 10054','forcibly closed','connection reset','remote end closed','connection aborted','broken pipe')):
                return 'reset'
            if any(x in text for x in ('timed out','timeout','name or service not known','getaddrinfo','connection refused','network is unreachable')):
                return 'service'
            if isinstance(exc,(ConnectionResetError,ConnectionAbortedError,BrokenPipeError)):
                return 'reset'
            if isinstance(exc,(TimeoutError,urllib.error.URLError)):
                return 'service'
            return ''

        failures=[]; bad_post_signal=False; service_signal=False; auth_signal=False
        for label,target in unique:
            # NZB retrieval is idempotent. Retry one remote reset locally before
            # falling through to the next same-indexer Newznab retrieval form.
            # This prevents a single TCP reset from becoming a raw WinError toast.
            for fetch_try in range(2):
                try:
                    return fetch(target)
                except urllib.error.HTTPError as exc:
                    code=int(getattr(exc,'code',0) or 0)
                    failures.append(f'{label}: HTTP {code}')
                    if code in {401,403}: auth_signal=True
                    elif code in {404,410}: bad_post_signal=True
                    elif code in {408,429,500,502,503,504}: service_signal=True
                    break
                except RuntimeError as exc:
                    # Search succeeded but the Newznab download endpoint returned a
                    # semantic error. Treat the exact result as unusable; the user can
                    # still clear the per-target blacklist manually if desired.
                    failures.append(f'{label}: {exc}')
                    bad_post_signal=True
                    break
                except Exception as exc:
                    kind=transient_kind(exc)
                    # Do not leak platform socket wording such as ``[WinError 10054]``
                    # into the release-search toast. Preserve the classification, not
                    # the OS-level exception text.
                    if kind=='reset':
                        failures.append(f'{label}: connection was reset while retrieving the NZB')
                        if fetch_try==0:
                            time.sleep(0.25)
                            continue
                        bad_post_signal=True
                    elif kind=='service':
                        failures.append(f'{label}: indexer connection failed or timed out')
                        service_signal=True
                    else:
                        failures.append(f'{label}: indexer request failed')
                        service_signal=True
                    break

        detail='; '.join(failures[-6:]) or 'request rejected'
        host=idx_name or (configured.hostname if configured else 'configured indexer')
        # A repeated connection reset/404/semantic failure for a result returned by
        # the current search is release-specific enough to remember as a bad post.
        # Pure authentication or broad service/network failures are not blacklisted.
        blacklist=bool(bad_post_signal and not (auth_signal and not bad_post_signal))
        if auth_signal and not bad_post_signal:
            raise ReleaseFetchError(f"Indexer authentication failed for {host}: {detail}", blacklist=False, error_code='indexer_auth')
        if service_signal and not bad_post_signal:
            raise ReleaseFetchError(f"Indexer could not be reached while fetching this NZB from {host}: {detail}", blacklist=False, error_code='indexer_unavailable')
        raise ReleaseFetchError(f"Indexer could not retrieve this NZB from {host}: {detail}", blacklist=blacklist, error_code='nzb_fetch_failed')

    def grab_release(self,data):
        title=str(data.get('title') or 'Indexer release')
        providers=[p for p in self.get_providers() if p.get('use_downloads',True) is not False]
        if not providers:
            raise ValueError('Add an NNTP provider enabled for downloads before grabbing a release')
        providers.sort(key=lambda p:(0 if str(p.get('role','primary'))=='primary' else 1,int(p.get('priority',10) or 10)))

        item_id=str(data.get('item_id') or '').strip()
        item=next((x for x in self._library() if str(x.get('id'))==item_id),None) if item_id else None
        parsed=data.get('parsed') if isinstance(data.get('parsed'),dict) else parse_release(title)
        manual_kind='tv' if str(data.get('media_kind') or '').lower()=='tv' else ('movie' if str(data.get('media_kind') or '').lower()=='movie' else '')
        manual_title=str(data.get('media_title') or '').strip()
        manual_year=int(data.get('media_year')) if str(data.get('media_year') or '').isdigit() else None
        manual_tmdb=int(data.get('media_tmdb_id') or 0) if str(data.get('media_tmdb_id') or '').isdigit() else None
        manual_item=None
        if not item and manual_kind and manual_title:
            profiles=self._profiles(); requested_profile=str(data.get('media_quality_profile_id') or '').strip(); profile=next((p for p in profiles if str(p.get('id') or '')==requested_profile),profiles[0])
            manual_item={'id':'','kind':manual_kind,'title':manual_title,'year':manual_year,'tmdb_id':manual_tmdb,
                         'quality_profile_id':str(profile.get('id') or ''),'root_folder':str(data.get('media_root_folder') or '').strip(),'movie_file':None,'seasons':[]}
        storage=self.release_storage_plan(item or manual_item,int(data.get('size') or 0)) if (item or manual_item) else None
        if (item or manual_item) and (not storage or not str((storage or {}).get('root') or '').strip()):
            raise ValueError(f"Add a {'TV' if (item or manual_item).get('kind')=='tv' else 'Movie'} root folder in Automation Setup before grabbing this media")
        if storage and not storage.get('ok_root'):
            raise ValueError(f"Not enough free space in the selected Root Folder for this release (free {storage.get('root_free',0)/1024**3:.1f} GB; requires about {storage.get('root_required',0)/1024**3:.1f} GB including reserve)")
        if storage and not storage.get('ok_staging'):
            raise ValueError(f"Not enough free space in the Download Folder for download/extraction (free {storage.get('staging_free',0)/1024**3:.1f} GB; requires about {storage.get('staging_required',0)/1024**3:.1f} GB including reserve)")

        context={}
        if item:
            season=data.get('season'); episode=data.get('episode')
            context={
                'source':'automation_grab','item_id':item_id,'kind':str(item.get('kind') or ''),
                'title':str(item.get('title') or ''),'year':item.get('year'),
                'season':int(season) if season is not None else None,
                'episode':int(episode) if episode is not None else None,
                'season_pack':bool(data.get('season_pack')),
                'pack_episode_numbers':[int(x) for x in (data.get('pack_episode_numbers') or []) if str(x).isdigit()][:200],
                'pack_known_episode_numbers':[int(x) for x in (data.get('pack_known_episode_numbers') or []) if str(x).isdigit()][:200],
                'episode_title':str(data.get('episode_title') or ''),
                'quality_profile_id':str(item.get('quality_profile_id') or ''),
                'release_title':title,'release_quality':str(parsed.get('quality') or 'Unknown'),
                'release_group':str(parsed.get('release_group') or ''),'indexer':str(data.get('indexer') or ''),
                'release_guid':str(data.get('guid') or data.get('download_url') or ''),
                'release_score':int(data.get('score') or 0),
                'planned_root_folder':str((storage or {}).get('root') or ''),
                'release_size':int(data.get('size') or 0),
                'automatic':bool(data.get('automatic',False)),
                'auto_type':str(data.get('auto_type') or ''),
                'target_key':str(data.get('target_key') or self._auto_target_key(context={
                    'item_id':item_id,'kind':str(item.get('kind') or ''),
                    'season':int(season) if season is not None else None,
                    'episode':int(episode) if episode is not None else None,
                    'season_pack':bool(data.get('season_pack'))
                })),
            }
        elif manual_item:
            season=data.get('season') if data.get('season') is not None else parsed.get('season')
            episode=data.get('episode') if data.get('episode') is not None else parsed.get('episode')
            season_pack=bool(data.get('season_pack') or parsed.get('is_season_pack'))
            episodes=[]; episode_title=str(data.get('episode_title') or '')
            if manual_kind=='tv':
                if season is None:
                    raise ValueError('This TV release does not identify a season or episode clearly enough for one-time Smart Import. Add the show to Automation for an ambiguous release.')
                try:
                    if manual_tmdb:
                        bundle=self._metadata_tv_bundle(manual_tmdb)
                        for sr in list((bundle or {}).get('seasons') or []):
                            if int(sr.get('season_number') or 0)!=int(season or 0): continue
                            for ep in list(sr.get('episodes') or []):
                                en=int(ep.get('episode_number') or 0)
                                if en>0: episodes.append({'season':int(season),'episode':en,'name':str(ep.get('name') or f'Episode {en}')})
                        if episode is not None:
                            hit=next((x for x in episodes if int(x.get('episode') or 0)==int(episode)),None)
                            if hit: episode_title=str(hit.get('name') or episode_title)
                except Exception:
                    episodes=[]
                if episode is not None and not episodes:
                    episodes=[{'season':int(season),'episode':int(episode),'name':episode_title or f'Episode {int(episode)}'}]
                if season_pack and not episodes:
                    raise ValueError('This season pack could not be matched to episode metadata safely. Add the show to Automation before grabbing the pack.')
            manual_key=f"manual:{manual_kind}:{manual_tmdb or (_norm(manual_title)+'-'+str(manual_year or ''))}"
            if manual_kind=='tv': manual_key+=f":s{int(season or 0):02d}" + (f":e{int(episode):03d}" if episode is not None else ':pack')
            context={
                'source':'manual_media_grab','one_time':True,'item_id':'','manual_item_id':manual_key,
                'kind':manual_kind,'title':manual_title,'year':manual_year,'tmdb_id':manual_tmdb,
                'metadata_provider':str(data.get('media_provider') or ('tmdb' if manual_tmdb else '')),
                'season':int(season) if season is not None else None,'episode':int(episode) if episode is not None else None,
                'season_pack':season_pack,'manual_episodes':episodes,'episode_title':episode_title,
                'quality_profile_id':str(manual_item.get('quality_profile_id') or ''),
                'release_title':title,'release_quality':str(parsed.get('quality') or 'Unknown'),
                'release_group':str(parsed.get('release_group') or ''),'indexer':str(data.get('indexer') or ''),
                'release_guid':str(data.get('guid') or data.get('download_url') or ''),
                'release_score':int(data.get('score') or 0),'planned_root_folder':str((storage or {}).get('root') or ''),
                'release_size':int(data.get('size') or 0),'automatic':False,'auto_type':'one_time',
                'target_key':manual_key,
            }

        target_key=str(context.get('target_key') or '')
        if target_key:
            try:
                snap=self.download_manager.snapshot()
                for job in snap.get('jobs') or []:
                    if not isinstance(job,dict): continue
                    ctx=job.get('automation_context') if isinstance(job.get('automation_context'),dict) else {}
                    if str(ctx.get('target_key') or '') != target_key: continue
                    status=str(job.get('status') or '')
                    post=str(job.get('post_status') or '')
                    if status in {'queued','downloading','retry_wait','cancelling'} or post in {'queued','verifying','repairing','extracting','importing','waiting'}:
                        return {
                            'ok':True,'already_queued':True,
                            'collection_id':str(job.get('collection_id') or job.get('id') or ''),
                            'collection_name':str(job.get('collection_name') or title),
                            'reason':'This media target is already downloading or being imported.'
                        }
            except Exception:
                pass

        claimed=True; reservation_path=Path(); reservation_payload={}
        if target_key:
            claimed,reservation_path,reservation_payload=self._claim_grab_reservation(target_key)
            if not claimed:
                return {
                    'ok':True,'already_queued':True,
                    'collection_id':str((reservation_payload or {}).get('collection_id') or ''),
                    'collection_name':title,
                    'reason':'Another NewzDeck runtime is already queueing this media target.'
                }

        try:
            # Fetch only after the target claim is held so two overlapping desktop/
            # service schedulers cannot both download and submit the same NZB.
            try:
                raw=self._fetch_release_nzb(data)
            except ReleaseFetchError as exc:
                if str(context.get('source') or '')=='automation_grab' and exc.blacklist:
                    self.record_release_failure(context,str(exc),error_code=exc.error_code)
                    raise ValueError(f"This release could not be retrieved from {str(data.get('indexer') or 'the indexer')} and has been marked FAILED for this target. Choose a different post. Details: {exc}") from exc
                raise ValueError(str(exc)) from exc

            # Submission/control-plane errors are not proof that the release itself
            # is bad. Only SAB's terminal history state may blacklist after queueing.
            try:
                queue_submit=getattr(self.download_manager,'queue_nzb',None)
                if callable(queue_submit):
                    result=queue_submit(str(providers[0].get('id')),title+'.nzb',raw,automation_context=context or None)
                else:
                    result=self.download_manager.add_nzb(str(providers[0].get('id')),title+'.nzb',raw,automation_context=context or None)
            except Exception as exc:
                # Never surface raw Windows socket/control-channel exceptions in the
                # Grab toast. They describe the private localhost SAB control path,
                # not the user's release. The download manager already performs the
                # safe ambiguity check/retry; this is the final UI boundary.
                low=str(exc or '').casefold()
                if any(x in low for x in ('winerror 10054','errno 10054','forcibly closed','connection reset','connection aborted','broken pipe','winerror 10061','errno 10061','connection refused')):
                    raise ValueError('The built-in download engine briefly lost its local connection while queueing this release. Check Downloads; if it is not listed, try Grab again in a moment.') from exc
                raise
            if target_key:
                self._finish_grab_reservation(reservation_path,reservation_payload,str(result.get('collection_id') or ''))
            event_message=(f"One-time media grab {title}" if str(context.get('source') or '')=='manual_media_grab' else f"{'Automatically grabbed' if data.get('automatic') else 'Grabbed'} {title}")
            self._event('grab',event_message,
                        collection=result.get('collection_name'),collection_id=result.get('collection_id'),
                        target_key=target_key,indexer=data.get('indexer'),item_id=item_id,
                        source=str(context.get('source') or ''),automatic=bool(data.get('automatic',False)))
            return result
        except Exception as exc:
            if target_key:
                self._release_grab_reservation(reservation_path)
            low=str(exc or '').casefold()
            if any(x in low for x in ('winerror 10054','errno 10054','forcibly closed','connection reset','connection aborted','broken pipe','remote end closed','winerror 10061','errno 10061','connection refused')):
                raise ValueError(_friendly_grab_exception(exc)) from exc
            raise
