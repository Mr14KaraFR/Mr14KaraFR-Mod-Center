import json,time,unittest
from pathlib import Path
from unittest.mock import patch
from discord_access import DiscordAccess,GITHUB_PREFIX
class BetaRelease(unittest.TestCase):
 def test_disabled_beta_is_hidden_even_for_beta_testers(self):
  from types import SimpleNamespace
  from unittest.mock import Mock
  from app import App
  config=json.loads((Path(__file__).parent/'channel.json').read_text(encoding='utf-8'))['discord_auth']
  client=DiscordAccess(config,GITHUB_PREFIX+'latest/download/catalog.json')
  view=SimpleNamespace(access=client,release_channel='beta',beta_button=Mock(),account_label=Mock(),login_button=Mock(),busy=False,refresh=Mock())
  account=dict(user=dict(name='QA'),subscriber=False,beta=True)
  App.update_account(view,account)
  App.toggle_beta(view)
  self.assertEqual(view.release_channel,'stable')
  view.beta_button.pack.assert_not_called()
  view.refresh.assert_not_called()
 def test_configured_beta_catalog_requires_beta_role(self):
  config=json.loads((Path(__file__).parent/'channel.json').read_text(encoding='utf-8'))['discord_auth']
  config['beta_catalog_url']=GITHUB_PREFIX+'latest/download/catalog-beta.json'
  client=DiscordAccess(config,GITHUB_PREFIX+'latest/download/catalog.json');client.session='test';client.expires=time.monotonic()+3600
  entry=dict(id='mr14karaecu',version='0.16.22',url=GITHUB_PREFIX+'download/modcenter-v0.3.2/Mr14KaraFR_Programmable_ECU.zip')
  for rights in [dict(beta=False,subscriber=False),dict(beta=False,subscriber=True)]:
   with patch.object(client,'account',return_value=rights),patch('discord_access.load_catalog') as load:
    with self.assertRaises(ValueError):client.catalog('beta')
    load.assert_not_called()
  with patch.object(client,'account',return_value=dict(beta=True,subscriber=False)),patch('discord_access.load_catalog',return_value=[entry.copy()]) as load:
   mods=client.catalog('beta');load.assert_called_once_with(config['beta_catalog_url']);self.assertEqual(mods[0]['access'],'beta');self.assertFalse(mods[0]['locked']);self.assertIsNone(client.download_headers(mods[0]))
  with patch.object(client,'account',return_value=dict(beta=False,subscriber=True)):
   with self.assertRaises(ValueError):client.download_headers(mods[0])
