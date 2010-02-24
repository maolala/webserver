# CTK: Cherokee Toolkit
#
# Authors:
#      Alvaro Lopez Ortega <alvaro@alobbs.com>
#
# Copyright (C) 2009 Alvaro Lopez Ortega
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public
# License as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

from Widget import Widget
from Container import Container


class TableField (Container):
    def __init__ (self, widget=None):
        Container.__init__ (self)
        self._props = {}
        self._tag   = 'td'

        if widget:
            Container.__add__ (self, widget)

    def Render (self):
        # Build tag props
        props = ''
        for p in self._props:
            value = self._props[p]
            if value:
                props += ' %s="%s"' %(p, value)
            else:
                props += ' %s' %(p)

        # Render content
        render = Container.Render(self)

        # Output
        html  = '<%s%s>' % (self._tag, props)
        html += render.html
        html += '</%s>' % (self._tag)

        render.html = html
        return render

    def __setitem__ (self, prop, value):
        assert type(prop)  == str
        assert type(value) == str

        self._props[prop] = value


class TableRow (Widget):
    def __init__ (self, length=1):
        Widget.__init__ (self)
        self.tag     = 'tr'
        self.props   = {}
        self.length  = length
        self.entries = [None] * length

    def __add__ (self, field):
        assert isinstance(field, TableField) or field == None
        self.entries.append (field)
        return self

    def __getitem__ (self, num):
        if num > self.length:
            raise IndexError, "Column number out of bounds (get)"

        return self.entries[num-1]

    def __setitem__ (self, num, field):
        assert isinstance(field, TableField) or field == None
        self.grow_to (num)
        self.entries[num-1] = field

    def grow_to (self, col):
        if col < 1:
            raise IndexError, "Column number out of bounds"

        if col > self.length:
            self.entries += [None] * (col - self.length)
            self.length = col

    def Render (self):
        # Render content
        render = Widget.Render(self)

        for field in self.entries:
            if field:
                render += field.Render()
            else:
                render.html += "<td></td>"

        # Wrap the table row
        props = " ".join (['%s="%s"'%(k,self.props[k]) for k in self.props])

        if props:
            render.html = '<%s %s>%s</%s>' %(self.tag, props, render.html, self.tag)
        else:
            render.html = '<%s>%s</%s>' %(self.tag, render.html, self.tag)

        return render


class Table (Widget):
    def __init__ (self, props=None, **kwargs):
        Widget.__init__ (self)
        self.kwargs      = kwargs
        self.last_row    = 0
        self.rows        = []
        self.props       = [{},props][bool(props)]
        self.header_rows = []
        self.header_cols = []

        if 'id' in self.props:
            self.id = self.props.pop('id')

    def __add_row (self):
        row = TableRow()
        self.rows.append (row)
        self.last_row += 1
        return row

    def __grow_if_needed (self, row, col):
        if row < 1:
            raise IndexError, "Row number out of bounds"

        while row > self.last_row:
            self.__add_row()

        for row in self.rows:
            row.grow_to (col)

    def __setitem_single (self, pos, widget):
        assert isinstance(widget, Widget) or widget is None
        assert type(pos) == tuple

        # Check table bounds
        row,col = pos
        self.__grow_if_needed (row, col)

        # The field object
        field = TableField (widget)

        # Set the element
        table_row = self.rows[row-1]
        table_row[col] = field

    def __setitem_list (self, pos, wid_list):
        row,col = pos
        for widget in wid_list:
            self.__setitem_single ((row,col), widget)
            col += 1

    def __setitem__ (self, pos, item):
        if type(item) == list:
            return self.__setitem_list (pos, item)
        else:
            return self.__setitem_single (pos, item)

    def __getitem__ (self, pos):
        # Whole row
        if type(pos) == int:
            if pos < 0:
                return self.rows[pos]
            return self.rows[pos-1]

        # Table cell
        row,col = pos

        if row > self.last_row:
            raise IndexError, "Row number out of bounds (get)"

        return self.rows[row-1][col]

    def __add__ (self, items):
        assert isinstance(items, list)
        self.__add_row()

        self[(self.last_row, 1)] = items
        return self

    def Render (self):
        # Set the header rows/cols
        for num in self.header_rows:
            for field in self.rows[num-1]:
                if field:
                    field._tag = 'th'

        for num in self.header_cols:
            for row in self.rows:
                row[num]._tag = 'th'

        # Render content
        render = Widget.Render (self)

        for row in self.rows:
            render += row.Render()

        # Wrap the table
        props = " ".join (['%s="%s"'%(k,self.props[k]) for k in self.props])
        if props:
            render.html = '<table id="%s" %s>%s</table>' %(self.id, props, render.html)
        else:
            render.html = '<table id="%s">%s</table>' %(self.id, render.html)

        return render

    def set_header (self, row=True, column=False, num=1):
        if column:
            self.header_cols.append(num)
            return

        if row:
            self.header_rows.append(num)
            return


class TableFixed (Table):
    def __init__ (self, rows, cols):
        Table.__init__ (self)
        self._fixed_rows = rows
        self._fixed_cols = cols

    def __setitem__ (self, pos, item):
        row,col = pos

        if row > self._fixed_rows:
            raise IndexError, "Row number out of bounds"

        if col > self._fixed_cols:
            raise IndexError, "Column number out of bounds"

        return Table.__setitem__ (self, pos, item)
