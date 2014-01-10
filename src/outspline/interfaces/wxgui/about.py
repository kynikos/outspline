# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Outspline.
#
# Outspline is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Outspline is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Outspline.  If not, see <http://www.gnu.org/licenses/>.

import wx
from datetime import datetime

from outspline.static.wxclasses.texturl import TextUrlCtrl
import outspline.coreaux_api as coreaux_api

_SIZE = 600


class AboutWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, wx.GetApp().root, title='About Outspline',
                          size=(_SIZE, _SIZE - 192),
                          style=wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER |
                                                          wx.MINIMIZE_BOX |
                                                          wx.MAXIMIZE_BOX) |
                          wx.FRAME_FLOAT_ON_PARENT)

        sizer1 = wx.GridBagSizer(4, 4)
        sizer1.AddGrowableRow(3)
        sizer1.AddGrowableCol(2)
        self.SetSizer(sizer1)

        logo = wx.StaticBitmap(self, bitmap=wx.ArtProvider.GetBitmap(
                                             'text-editor', wx.ART_CMN_DIALOG))

        name = wx.StaticText(self, label='Outspline')
        name.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC,
                             wx.FONTWEIGHT_BOLD))

        version = wx.StaticText(self, label='version: {} ({})'.format(
                                coreaux_api.get_main_component_version(),
                                coreaux_api.get_main_component_release_date()))

        self.copyright = wx.StaticText(self, label=coreaux_api.get_copyright(
                                                                      alt=True))
        self.copyright.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT,
                                       wx.FONTSTYLE_NORMAL,
                                       wx.FONTWEIGHT_NORMAL))

        self.website = wx.HyperlinkCtrl(self, wx.ID_ANY,
                                        label=coreaux_api.get_website(),
                                        url=coreaux_api.get_website())

        description = wx.StaticText(self,
                                    label=coreaux_api.get_long_description())
        description.Wrap(_SIZE - 8)

        info = InfoBox(self)

        button = wx.Button(self, label='Close')

        sizer1.Add(logo, (0, 0), span=(2, 1), flag=wx.ALIGN_CENTER | wx.LEFT |
                   wx.TOP | wx.RIGHT, border=8)
        sizer1.Add(name, (0, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.TOP,
                   border=8)
        sizer1.Add(version, (0, 2), flag=wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM |
                   wx.RIGHT, border=8)
        sizer1.Add(self.copyright, (1, 1), flag=wx.ALIGN_LEFT |
                   wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.website, (1, 2), flag=wx.ALIGN_RIGHT |
                   wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=8)
        sizer1.Add(description, (2, 0), span=(1, 3), flag=wx.ALL, border=4)
        sizer1.Add(info, (3, 0), span=(1, 3), flag=wx.LEFT | wx.RIGHT |
                   wx.EXPAND, border=4)
        sizer1.Add(button, (4, 0), span=(1, 3), flag=wx.ALIGN_CENTER |
                   wx.BOTTOM, border=4)

        self.Bind(wx.EVT_BUTTON, self.close, button)

        self.Centre()
        self.Show(True)

    def close(self, event):
        self.Destroy()


class InfoBox(wx.SplitterWindow):
    tree = None
    textw = None
    STYLE_HEAD = None
    STYLE_NORMAL = None
    STYLE_BOLD = None
    STYLE_ITALIC = None

    def __init__(self, parent):
        wx.SplitterWindow.__init__(self, parent, style=wx.SP_LIVE_UPDATE)

        self.tree = wx.TreeCtrl(self, style=wx.TR_HAS_BUTTONS |
                                wx.TR_HIDE_ROOT | wx.TR_SINGLE |
                                wx.TR_FULL_ROW_HIGHLIGHT | wx.BORDER_SUNKEN)

        self.STYLE_HEAD = wx.TextAttr(font=wx.Font(14, wx.FONTFAMILY_DEFAULT,
                                                   wx.FONTSTYLE_NORMAL,
                                                   wx.FONTWEIGHT_BOLD))
        self.STYLE_NORMAL = wx.TextAttr(font=wx.Font(10, wx.FONTFAMILY_DEFAULT,
                                                     wx.FONTSTYLE_NORMAL,
                                                     wx.FONTWEIGHT_NORMAL))
        self.STYLE_BOLD = wx.TextAttr(font=wx.Font(10, wx.FONTFAMILY_DEFAULT,
                                                   wx.FONTSTYLE_NORMAL,
                                                   wx.FONTWEIGHT_BOLD))
        self.STYLE_ITALIC = wx.TextAttr(font=wx.Font(10, wx.FONTFAMILY_DEFAULT,
                                                     wx.FONTSTYLE_ITALIC,
                                                     wx.FONTWEIGHT_NORMAL))

        self.tree.AddRoot(text='root')
        self.init_info()

        self.textw = TextUrlCtrl(self, value='', style=wx.TE_MULTILINE |
                            wx.TE_READONLY | wx.TE_DONTWRAP | wx.BORDER_SUNKEN)

        self.SplitVertically(self.tree, self.textw)

        # Prevent the window from unsplitting when dragging the sash to the
        # border
        self.SetMinimumPaneSize(20)
        self.SetSashPosition(120)

        self.Bind(wx.EVT_SPLITTER_DCLICK, self.veto_dclick)
        self.tree.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.veto_label_edit)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.retrieve_info)

        self.tree.SelectItem(self.tree.GetFirstChild(self.tree.GetRootItem())[0
                                                                             ])

    def init_info(self):
        self.tree.AppendItem(self.tree.GetRootItem(), text='License',
                             data=wx.TreeItemData({'req': 'lic'}))

        self.tree.AppendItem(self.tree.GetRootItem(), text='Info',
                             data=wx.TreeItemData({'req': 'cor'}))

        # Do not use the configuration because it could have entries about
        # addons that aren't actually installed
        info = coreaux_api.get_addons_info()

        for type_ in ('Extensions', 'Interfaces', 'Plugins'):
            typeitem = self.tree.AppendItem(self.tree.GetRootItem(), text=type_,
                           data=wx.TreeItemData({'req': 'lst', 'type_': type_}))
            for addon in info(type_).get_sections():
                self.tree.AppendItem(typeitem, text=addon, data=wx.TreeItemData(
                                {'req': 'inf', 'type_': type_, 'addon': addon}))

    def compose_license(self):
        self.textw.AppendText('{}\n{}\n\n{}'.format(
                                                  coreaux_api.get_description(),
                                                  coreaux_api.get_copyright(),
                                                  coreaux_api.get_disclaimer()))

    def compose_main_info(self):
        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('Core version: ')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        self.textw.AppendText(coreaux_api.get_core_version())

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nWebsite: ')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        self.textw.AppendText(coreaux_api.get_website())

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nAuthor: ')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        self.textw.AppendText('Dario Giovannetti <dev@dariogiovannetti.net>')

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nContributors: ')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        for c in coreaux_api.get_core_contributors():
            self.textw.AppendText('\n\t{}'.format(c))

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\n\nInstalled components:')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        cinfo = coreaux_api.get_components_info()
        for c in cinfo('Components').get_sections():
            self.textw.AppendText('\n\t{} {} ({})'.format(c,
                                              cinfo('Components')(c)['version'],
                                        cinfo('Components')(c)['release_date']))

    def compose_addon_info(self, type_, addon):
        info = coreaux_api.get_addons_info()(type_)(addon)
        config = coreaux_api.get_configuration()(type_)(addon)

        self.textw.SetDefaultStyle(self.STYLE_HEAD)
        self.textw.AppendText('{}\n'.format(addon))

        self.textw.SetDefaultStyle(self.STYLE_NORMAL)

        self.textw.AppendText('{}\n'.format(info['description']))

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nEnabled: ')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        self.textw.AppendText('yes' if config.get_bool('enabled') else 'no')

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nVersion: ')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        self.textw.AppendText(info['version'])

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nWebsite: ')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        self.textw.AppendText(info['website'])

        authors = []
        contributors = []
        dependencies = []
        optionaldependencies = []
        for o in info.get_options():
            if o[:6] == 'author':
                authors.append(info[o])
            elif o[:11] == 'contributor':
                contributors.append(info[o])
            elif o[:10] == 'dependency':
                dependencies.append(info[o])
            elif o[:19] == 'optional_dependency':
                optionaldependencies.append(info[o])

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        if len(authors) > 1:
            self.textw.AppendText('\nAuthors:')
            self.textw.SetDefaultStyle(self.STYLE_NORMAL)
            for a in authors:
                self.textw.AppendText('\n\t{}'.format(a))
        else:
            self.textw.AppendText('\nAuthor: ')
            self.textw.SetDefaultStyle(self.STYLE_NORMAL)
            self.textw.AppendText(authors[0])

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nContributors:')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        for c in contributors:
            self.textw.AppendText('\n\t{}'.format(c))

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nComponent: ')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        cinfo = coreaux_api.get_components_info()
        component = cinfo(type_)(addon)[info['version']]
        self.textw.AppendText('{} {} ({})'.format(component,
                                      cinfo('Components')(component)['version'],
                                cinfo('Components')(component)['release_date']))

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nDependencies:')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        for d in dependencies:
            self.textw.AppendText('\n\t{}.x'.format(d))

        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('\nOptional dependencies:')
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        for o in optionaldependencies:
            self.textw.AppendText('\n\t{}.x'.format(o))

    def compose_list(self, type_):
        # Do not use the configuration because it could have entries about
        # addons that aren't actually installed
        info = coreaux_api.get_addons_info()
        self.textw.SetDefaultStyle(self.STYLE_BOLD)
        self.textw.AppendText('{}:\n'.format(type_))
        for addon in info(type_).get_sections():
            config = coreaux_api.get_configuration()(type_)(addon)
            if config.get_bool('enabled'):
                self.textw.SetDefaultStyle(self.STYLE_NORMAL)
                self.textw.AppendText('\t{}\n'.format(addon))
            else:
                self.textw.SetDefaultStyle(self.STYLE_ITALIC)
                self.textw.AppendText('\t{} [disabled]\n'.format(addon))

    def veto_dclick(self, event):
        event.Veto()

    def veto_label_edit(self, event):
        event.Veto()

    def retrieve_info(self, event):
        self.textw.Clear()
        self.textw.SetDefaultStyle(self.STYLE_NORMAL)
        data = self.tree.GetPyData(event.GetItem())
        if data['req'] == 'lic':
            self.compose_license()
        elif data['req'] == 'cor':
            self.compose_main_info()
        elif data['req'] == 'lst':
            self.compose_list(data['type_'])
        elif data['req'] == 'inf':
            self.compose_addon_info(data['type_'], data['addon'])
        # Scroll back to top
        self.textw.ShowPosition(0)
