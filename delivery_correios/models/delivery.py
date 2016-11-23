# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from pysigep.sigep import BuscaCliente
    from pysigep.sigep import CalcularPrecoPrazo
except ImportError:
    _logger.debug('Cannot import pysigepweb')


class CorreiosServicos(models.Model):
    _name = 'delivery.correios.service'

    code = fields.Char(string="Código", size=20)
    identifier = fields.Char(string="Identificador", size=20)
    name = fields.Char(string="Descrição", size=70)
    delivery_id = fields.Many2one('delivery.carrier', string="Método entrega")


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    correio_login = fields.Char(string="Login Correios", size=30)
    correio_password = fields.Char(string="Senha do Correio", size=30)
    cod_administrativo = fields.Char(string="Código Administrativo", size=20)
    num_contrato = fields.Char(string="Número de Contrato", size=20)
    cartao_postagem = fields.Char(
        string="Número do cartão de Postagem", size=20)

    delivery_type = fields.Selection(
        selection_add=[('correios', 'Correios')])
    service_id = fields.Many2one('delivery.correios.service', string="Serviço")
    service_ids = fields.One2many('delivery.correios.service', 'delivery_id')

    @api.one
    def action_get_correio_services(self):
        req = BuscaCliente(self.num_contrato, self.cartao_postagem,
                           self.correio_login, self.correio_password)

        objeto_resposta = req.execute()

        self.service_ids.unlink()
        for item in objeto_resposta.contratos.cartoesPostagem.servicos:
            self.env['delivery.correios.service'].create({
                'code': item.codigo,
                'identifier': item.id,
                'name': item.descricao,
                'delivery_id': self.id,
            })

    def correios_get_shipping_price_from_so(self, orders):
        ''' For every sale order, compute the price of the shipment

        :param orders: A recordset of sale orders
        :return list: A list of floats, containing the estimated price for the
         shipping of the sale order
        '''
        custos = []
        for order in orders:
            custo = 0.0
            if not self.service_id:
                raise UserError(u'Escolha o tipo de serviço para poder \
                                calcular corretamente o frete dos correios')

            cod_administrativo = self.cod_administrativo
            senha = self.correio_password
            codigo_servico = self.service_id.code
            origem = '88032-050'
            destino = '88037-240'
            peso = '0.650'
            formato = 1
            comprimento = altura = largura = 30.0
            diametro = 0.0
            mao_propria = 'N'
            valor_declarado = 0.0
            aviso_recebimento = 'N'
            consulta = CalcularPrecoPrazo(cod_administrativo, senha,
                                          codigo_servico, origem, destino,
                                          peso, formato, comprimento, altura,
                                          largura, diametro, mao_propria,
                                          valor_declarado, aviso_recebimento)
            resposta = consulta.execute()
            if int(resposta.Servicos.cServico.Erro) != 0:
                raise UserError(resposta.Servicos.cServico.MsgErro)
            valor = str(resposta.Servicos.cServico.Valor).replace(',', '.')
            custo = float(valor)
            custos.append(custo)

        return custos

    def correios_send_shipping(self, pickings):
        ''' Send the package to the service provider

        :param pickings: A recordset of pickings
        :return list: A list of dictionaries (one per picking) containing of
                    the form::
                         { 'exact_price': price,
                           'tracking_number': number }
        '''
        return [{
            'exact_price': 22.67,
            'tracking_number': 123
        }]

    def correios_get_tracking_link(self, pickings):
        ''' Ask the tracking link to the service provider

        :param pickings: A recordset of pickings
        :return list: A list of string URLs, containing the tracking links
         for every picking
        '''
        # TODO Retornar a url correta aqui
        return ['http://www.google.com']

    def correios_cancel_shipment(self):
        ''' Cancel a shipment

        :param pickings: A recordset of pickings
        '''
        pass
