from django.utils.translation import gettext_lazy as _
from django.utils.html import json_script
from draftjs_exporter.dom import DOM
from draftjs_exporter.defaults import render_children
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    Block,
    BLOCK_KEY_NAME,
    BlockElementHandler,
    ListElementHandler,
    ListItemElementHandler,
)
from wagtail.admin.rich_text.editors.draftail.features import (
    ControlFeature,
)
from wagtail import hooks


@hooks.register("register_icons")
def register_icons(icons):
    return icons + [
        "wagtail_text_alignment/text-left.svg",
        "wagtail_text_alignment/text-center.svg",
        "wagtail_text_alignment/text-right.svg",
    ]


@hooks.register('insert_global_admin_js')
def global_admin_js():
    # For translating alignments in the Draftail editor
    # See rt_extensions/alignment.js
    return json_script({
            "left": _("Align Left"),
            "center": _("Align Center"),
            "right": _("Align Right"),
        },
        "wagtail-text-alignment-i18n",
    )


def text_alignment_elem(tag_name):
    """
        A utility function for creating elements with the
        data-alignment attribute set.
    """
    def text_alignment(props):

        if "block" in props and "data" in props["block"]:
            alignment = props["block"]["data"].get("alignment", "left")
            return DOM.create_element(
                tag_name,
                {
                    "data-alignment": alignment,
                    "class": f"text-{alignment}",
                },
                render_children(props),
            )

        return DOM.create_element(
            tag_name,
            {"data-alignment": "left"},
            render_children(props),
        )
    
    text_alignment.__name__ = f"text_alignment_{tag_name}"
    text_alignment.__repr__ = lambda self: f"text_alignment_{tag_name}"
    
    return text_alignment


def _new_alignment_handler(tag_name, block_type, base_class = BlockElementHandler):

    handler_class = AlignmentHandler(base_class=base_class)
    if issubclass(base_class, ListItemElementHandler):
        handler = handler_class()
    else:
        handler = handler_class(block_type)
    
    return {
        f"{tag_name}[data-alignment='left']":   handler,
        f"{tag_name}[data-alignment='center']": handler,
        f"{tag_name}[data-alignment='right']":  handler,
    }



class AlignmentBlock(Block):
    """
        Block for persisting data-alignment attribute.
        The data attribute is omitted by default.
    """
    def __init__(self, typ, depth=0, key=None, alignment=None):
        super().__init__(typ, depth, key)
        self.data = {"alignment": alignment or "left"}

    def as_dict(self):
        return super().as_dict() | {
            "data": self.data,
        }


def AlignmentHandler(base_class = BlockElementHandler):
    class AlignHandler(base_class):
        """
        Draft.js block handler for alignment blocks.
        """

        mutability = "MUTABLE"

        def create_block(self, name, attrs, state, contentstate):
            if issubclass(base_class, ListItemElementHandler):
                assert state.list_item_type is not None, (
                    "%s element found outside of an enclosing list element" % name
                )

                init_kwarg = state.list_item_type
            else:
                init_kwarg = self.block_type
                
            return AlignmentBlock(
                init_kwarg, depth=state.list_depth, key=attrs.get(BLOCK_KEY_NAME),
                alignment=attrs.get("data-alignment", "left"),
            )
    return AlignHandler



_BLOCK_TYPES = (
    ("unstyled", "p", BlockElementHandler),
    ("header-one", "h1", BlockElementHandler),
    ("header-two", "h2", BlockElementHandler),
    ("header-three", "h3", BlockElementHandler),
    ("header-four", "h4", BlockElementHandler),
    ("header-five", "h5", BlockElementHandler),
    ("header-six", "h6", BlockElementHandler),
    ("blockquote", "blockquote", BlockElementHandler),
    ("code-block", "pre", BlockElementHandler),
    # ("unordered-list-item", "li", ListItemElementHandler),
    # ("ordered-list-item", "li", ListItemElementHandler),
)



@hooks.register("wagtail_text_alignment.register_block_types")
def register_list_types(block_map, from_db_format):
    block_map["ordered-list-item"] = {
        "element": text_alignment_elem("li"),
        "wrapper": "ol",
    }
    block_map["unordered-list-item"] = {
        "element": text_alignment_elem("li"),
        "wrapper": "ul",
    }

    # block_type is not used for ListItemElementHandler.
    from_db_format.update(
        _new_alignment_handler(
            "li", None, ListItemElementHandler,
        )
    )

    return block_map, from_db_format


@hooks.register('register_rich_text_features', order=-1)
def register_richtext_alignment_features(features):
    feature_name = "text-alignment"

    # Register the control feature (plugin is also included in the JS)
    features.register_editor_plugin(
        "draftail",
        feature_name,
        ControlFeature({
                "type": feature_name,
            },
            js=[
                "wagtail_text_alignment/alignment.js",
            ],
            css={"all": ["wagtail_text_alignment/alignment.css"]},
        ),
    )

    block_map = {}
    from_db_format = {}

    for block_type, tag_name, base_class in _BLOCK_TYPES:
        block_map[block_type] = text_alignment_elem(tag_name)
        from_db_format.update(
            _new_alignment_handler(tag_name, block_type, base_class)
        )

    for fn in hooks.get_hooks('wagtail_text_alignment.register_block_types'):
        block_map, from_db_format = fn(block_map, from_db_format)

    config = {
        "to_database_format": {
            "block_map": block_map,
        },
        "from_database_format": from_db_format,
    }

    for fn in hooks.get_hooks('wagtail_text_alignment.construct_alignment_config'):
        config = fn(config)

    features.register_converter_rule('contentstate', feature_name, config)
